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
"""

import hashlib
from typing import Optional, Tuple

from secp256k1 import PrivateKey, PublicKey


def hash_to_curve(message: bytes) -> PublicKey:
    """Generates a point from the message hash and checks if the point lies on the curve.
    If it does not, it tries computing a new point from the hash."""
    point = None
    msg_to_hash = message
    while point is None:
        _hash = hashlib.sha256(msg_to_hash).digest()
        try:
            point = PublicKey(b"\x02" + _hash, raw=True)
        except Exception:
            msg_to_hash = _hash
    return point


def step1_alice(
    secret_msg: str, blinding_factor: Optional[PrivateKey] = None
) -> tuple[PublicKey, PrivateKey]:
    Y: PublicKey = hash_to_curve(secret_msg.encode("utf-8"))
    r = blinding_factor or PrivateKey()
    B_: PublicKey = Y + r.pubkey  # type: ignore
    return B_, r


def step2_bob(B_: PublicKey, a: PrivateKey) -> PublicKey:
    C_: PublicKey = B_.mult(a)  # type: ignore
    return C_


def step3_alice(C_: PublicKey, r: PrivateKey, A: PublicKey) -> PublicKey:
    C: PublicKey = C_ - A.mult(r)  # type: ignore
    return C


def verify(a: PrivateKey, C: PublicKey, secret_msg: str) -> bool:
    Y: PublicKey = hash_to_curve(secret_msg.encode("utf-8"))
    return C == Y.mult(a)  # type: ignore


# stamps
"""
Proves that a in A = a*G is the same as a in C = a*Y

Bob:
R1 = rG
R2 = rY
e = hash(R1, R2, Y, C)
s = r + e*a

Alice/Carol:
Y = hash_to_curve(x)
R1 = sG - eA
R2 = sY - eC
    (eaY = eC, since C' - rA = aY + arG - arG = aY = C)

e == hash(R1, R2, Y, C) (verification)

If true, C must have originated from Bob with private key a
"""


def hash_e(*args) -> bytes:
    """Hashes a list of public keys to a 32 byte value"""
    e_ = ""
    for pk in args:
        assert isinstance(pk, PublicKey), "object is not of type PublicKey"
        e_ += pk.serialize(compressed=False).hex()
    e = hashlib.sha256(e_.encode("utf-8")).digest()
    return e


def stamp_step1_bob(
    Y: PublicKey, C: PublicKey, a: PrivateKey, p_bytes: bytes = b""
) -> Tuple[PrivateKey, PrivateKey]:
    if p_bytes:
        # deterministic p for testing
        p = PrivateKey(privkey=p_bytes, raw=True)
    else:
        # normally, we generate a random p
        p = PrivateKey()
    assert p.pubkey
    R1: PublicKey = p.pubkey  # R1 = pG
    R2: PublicKey = Y.mult(p)  # type: ignore # R2 = pY
    print(R1.serialize().hex(), R2.serialize().hex())
    e = hash_e(R1, R2, Y, C)
    s = p.tweak_add(a.tweak_mul(e))  # s = p + ea
    spk = PrivateKey(s, raw=True)
    epk = PrivateKey(e, raw=True)
    return epk, spk


def stamp_step2_alice_verify(
    Y: PublicKey, C: PublicKey, s: PrivateKey, e: PrivateKey, A: PublicKey
) -> bool:
    assert s.pubkey
    R1: PublicKey = s.pubkey - A.mult(e)  # type: ignore # R1 = sG - eA
    R2: PublicKey = Y.mult(s) - C.mult(e)  # type: ignore # R2 = sY - eC
    e_bytes = e.private_key
    return e_bytes == hash_e(R1, R2, Y, C)


# Below is a test of a simple positive and negative case

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
