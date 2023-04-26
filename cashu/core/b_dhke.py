# Don't trust me with cryptography.

"""
Implementation of https://gist.github.com/RubenSomsen/be7a4760dd4596d06963d67baf140406

Bob (Mint):
A = a*G
return A

Alice (Client):
Y = hash_to_curve(secret_message)
r = random blinding factor
B'= Y + r*G
return B'

Bob:
C' = a*B'
  (= a*Y + a*r*G)
return C'

Alice:
C = C' - r*A
 (= C' - a*r*G)
 (= a*Y)
return C, secret_message

Bob:
Y = hash_to_curve(secret_message)
C == a*Y
If true, C must have originated from Bob


# DLEQ Proof

(These steps occur once Bob returns C')

Bob:
 r = random nonce
R1 = r*G
R2 = r*B'
 e = hash(R1,R2,A,C')
 s = r + e*a
return e, s

Alice:
R1 = s*G - e*A
R2 = s*B' - e*C'
e == hash(R1,R2,A,C')

If true, a in A = a*G must be equal to a in C' = a*B'
"""

import hashlib

from secp256k1 import PrivateKey, PublicKey


def hash_to_curve(message: bytes) -> PublicKey:
    """Generates a point from the message hash and checks if the point lies on the curve.
    If it does not, it tries computing a new point from the hash."""
    point = None
    msg_to_hash = message
    while point is None:
        try:
            _hash = hashlib.sha256(msg_to_hash).digest()
            point = PublicKey(b"\x02" + _hash, raw=True)
        except:
            msg_to_hash = _hash
    return point


def step1_alice(
    secret_msg: str, blinding_factor: bytes = None
) -> tuple[PublicKey, PrivateKey]:
    Y: PublicKey = hash_to_curve(secret_msg.encode("utf-8"))
    if blinding_factor:
        r = PrivateKey(privkey=blinding_factor, raw=True)
    else:
        r = PrivateKey()
    B_: PublicKey = Y + r.pubkey
    return B_, r


def step2_bob(B_: PublicKey, a: PrivateKey):
    C_ = B_.mult(a)

    # produce dleq proof
    e, s = step2_bob_dleq(B_, a)
    return C_, e, s


def step3_alice(C_: PublicKey, r: PrivateKey, A: PublicKey) -> PublicKey:
    C: PublicKey = C_ - A.mult(r)
    return C


def verify(a: PrivateKey, C: PublicKey, secret_msg: str) -> bool:
    Y: PublicKey = hash_to_curve(secret_msg.encode("utf-8"))
    return C == Y.mult(a)


# DLEQ

# Bob:
#  r = random nonce
# R1 = r*G
# R2 = r*B'
#  e = hash(R1,R2,A,C')
#  s = r + e*a
# return e, s

# Alice:
# R1 = s*G - e*A
# R2 = s*B' - e*C'
# e == hash(R1,R2,A,C')


def hash_e(R1: PublicKey, R2: PublicKey, K: PublicKey, C_: PublicKey):
    _R1 = R1.serialize(compressed=False).hex()
    _R2 = R2.serialize(compressed=False).hex()
    _K = K.serialize(compressed=False).hex()
    _C_ = C_.serialize(compressed=False).hex()
    e_ = f"{_R1}{_R2}{_K}{_C_}"
    e = hashlib.sha256(e_.encode("utf-8")).digest()
    return e


def step2_bob_dleq(B_: PublicKey, a: PrivateKey):
    p = PrivateKey()  # generate random value
    R1 = p.pubkey  # R1 = pG
    R2 = B_.mult(p)  # R2 = pB_
    print(f"R1 is: {R1.serialize().hex()}")
    print(f"R2 is: {R2.serialize().hex()}")
    C_ = B_.mult(a)  # C_ = aB_
    K = a.pubkey
    e = hash_e(R1, R2, K, C_)  # e = hash(R1, R2, K, C_)
    s = p.tweak_add(a.tweak_mul(e))  # s = p + ek
    return e, s


def alice_verify_dleq(e: bytes, s: bytes, A: PublicKey, B_: bytes, C_: bytes):
    epk = PrivateKey(e, raw=True)
    spk = PrivateKey(s, raw=True)
    bk = PublicKey(B_, raw=True)
    ck = PublicKey(C_, raw=True)
    R1 = spk.pubkey - A.mult(epk)
    R2 = bk.mult(spk) - ck.mult(epk)
    print(f"R1 is: {R1.serialize().hex()}")
    print(f"R2 is: {R2.serialize().hex()}")
    if e == hash_e(R1, R2, A, ck):
        print("DLEQ proof ok!")
    else:
        print("DLEQ proof broken")
    return e == hash_e(R1, R2, A, ck)


### Below is a test of a simple positive and negative case

# # Alice's keys
# a = PrivateKey()
# A = a.pubkey
# secret_msg = "test"
# B_, r = step1_alice(secret_msg)
# C_ = step2_bob(B_, a)
# C = step3_alice(C_, r, A)
# print("C:{}, secret_msg:{}".format(C, secret_msg))
# assert verify(a, C, secret_msg)
# assert verify(a, C + C, secret_msg) == False  # adding C twice shouldn't pass
# assert verify(a, A, secret_msg) == False  # A shouldn't pass

# # Test operations
# b = PrivateKey()
# B = b.pubkey
# assert -A -A + A == -A  # neg
# assert B.mult(a) == A.mult(b)  # a*B = A*b
