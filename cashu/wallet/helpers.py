import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

import click
from loguru import logger

from ..core.base import TokenV1, TokenV2, TokenV3, TokenV3Token
from ..core.helpers import sum_proofs
from ..core.migrations import migrate_databases
from ..core.settings import settings
from ..wallet import migrations
from ..wallet.crud import get_keyset, get_unused_locks
from ..wallet.wallet import Wallet as Wallet


async def init_wallet(wallet: Wallet, load_proofs: bool = True):
    """Performs migrations and loads proofs from db."""
    await migrate_databases(wallet.db, migrations)
    if load_proofs:
        await wallet.load_proofs(reload=True)


async def redeem_TokenV3_multimint(
    wallet: Wallet,
    token: TokenV3,
    secret_lock_script: Optional[str] = None,
    secret_lock_signature: Optional[str] = None,
    secret_p2pk_signatures: Optional[List[str]] = None,
):
    """
    Helper function to iterate thruogh a token with multiple mints and redeem them from
    these mints one keyset at a time.
    """
    for t in token.token:
        assert t.mint, Exception(
            "redeem_TokenV3_multimint: multimint redeem without URL"
        )
        mint_wallet = Wallet(t.mint, os.path.join(settings.cashu_dir, wallet.name))
        keysets = mint_wallet._get_proofs_keysets(t.proofs)
        logger.debug(f"Keysets in tokens: {keysets}")
        # loop over all keysets
        for keyset in set(keysets):
            await mint_wallet.load_mint()
            # redeem proofs of this keyset
            redeem_proofs = [p for p in t.proofs if p.id == keyset]
            _, _ = await mint_wallet.redeem(
                redeem_proofs,
                secret_lock_script=secret_lock_script,
                secret_lock_signature=secret_lock_signature,
                secret_p2pk_signatures=secret_p2pk_signatures,
            )
            print(f"Received {sum_proofs(redeem_proofs)} sats")


def serialize_TokenV2_to_TokenV3(tokenv2: TokenV2):
    """Helper function to receive legacy TokenV2 tokens.
    Takes a list of proofs and constructs a *serialized* TokenV3 to be received through
    the ordinary path.

    Returns:
        TokenV3: TokenV3
    """
    tokenv3 = TokenV3(token=[TokenV3Token(proofs=tokenv2.proofs)])
    if tokenv2.mints:
        tokenv3.token[0].mint = tokenv2.mints[0].url
    token_serialized = tokenv3.serialize()
    return token_serialized


def serialize_TokenV1_to_TokenV3(tokenv1: TokenV1):
    """Helper function to receive legacy TokenV1 tokens.
    Takes a list of proofs and constructs a *serialized* TokenV3 to be received through
    the ordinary path.

    Returns:
        TokenV3: TokenV3
    """
    tokenv3 = TokenV3(token=[TokenV3Token(proofs=tokenv1.__root__)])
    token_serialized = tokenv3.serialize()
    return token_serialized


def deserialize_token_from_string(token: str) -> TokenV3:
    # deserialize token

    # ----- backwards compatibility -----

    # V2Tokens (0.7-0.11.0) (eyJwcm9...)
    if token.startswith("eyJwcm9"):
        try:
            tokenv2 = TokenV2.parse_obj(json.loads(base64.urlsafe_b64decode(token)))
            token = serialize_TokenV2_to_TokenV3(tokenv2)
        except:
            pass

    # V1Tokens (<0.7) (W3siaWQ...)
    if token.startswith("W3siaWQ"):
        try:
            tokenv1 = TokenV1.parse_obj(json.loads(base64.urlsafe_b64decode(token)))
            token = serialize_TokenV1_to_TokenV3(tokenv1)
        except:
            pass

    # ----- receive token -----

    # deserialize token
    # dtoken = json.loads(base64.urlsafe_b64decode(token))
    tokenObj = TokenV3.deserialize(token)

    # tokenObj = TokenV2.parse_obj(dtoken)
    assert len(tokenObj.token), Exception("no proofs in token")
    assert len(tokenObj.token[0].proofs), Exception("no proofs in token")
    return tokenObj


async def receive(
    wallet: Wallet,
    tokenObj: TokenV3,
):
    proofs = [p for t in tokenObj.token for p in t.proofs]

    # load for P2SH scripts and and sign P2PK locks
    script, signature, p2pk_signatures = None, None, None

    # P2SH scripts
    if all([p.secret.startswith("P2SH:") for p in proofs]):
        address_split = proofs[0].secret.split(":")[1]
        p2shscripts = await get_unused_locks(address_split, db=wallet.db)
        assert len(p2shscripts) == 1, Exception("lock not found.")
        script, signature = p2shscripts[0].script, p2shscripts[0].signature
    # P2PK signatures
    elif all([p.secret.startswith("P2PK:") for p in proofs]):
        p2pk_signatures = await wallet.sign_p2pk_with_privatekey(proofs)

    includes_mint_info: bool = any([t.mint for t in tokenObj.token])

    if includes_mint_info:
        # redeem tokens with new wallet instances
        await redeem_TokenV3_multimint(
            wallet,
            tokenObj,
            script,
            signature,
            p2pk_signatures,
        )
    else:
        # this is very legacy code, virtually any token should have mint information
        # no mint information present, we extract the proofs and use wallet's default mint
        # first we load the mint URL from the DB
        keyset_in_token = proofs[0].id
        assert keyset_in_token
        # we get the keyset from the db
        mint_keysets = await get_keyset(id=keyset_in_token, db=wallet.db)
        assert mint_keysets, Exception("we don't know this keyset")
        assert mint_keysets.mint_url, Exception("we don't know this mint's URL")
        # now we have the URL
        mint_wallet = Wallet(
            mint_keysets.mint_url,
            os.path.join(settings.cashu_dir, wallet.name),
        )
        await mint_wallet.load_mint(keyset_in_token)
        _, _ = await mint_wallet.redeem(proofs, script, signature, p2pk_signatures)
        print(f"Received {sum_proofs(proofs)} sats")

    # reload main wallet so the balance updates
    await wallet.load_proofs(reload=True)
    wallet.status()
    return wallet.available_balance


async def send(
    wallet: Wallet, amount: int, lock: str, legacy: bool, split: bool = True
):
    """
    Prints token to send to stdout.
    """
    if lock:
        assert len(lock) > 21, Exception(
            "Error: lock has to be at least 22 characters long."
        )
        if not lock.startswith("P2SH:") and not lock.startswith("P2PK:"):
            raise Exception("Error: lock has to start with P2SH: or P2PK:")
        # we add a time lock to the P2PK lock by appending the current unix time + 14 days
        # we use datetime because it's easier to read
        if lock.startswith("P2PK:") or lock.startswith("P2SH:"):
            logger.debug(f"Locking token to: {lock}")
            logger.debug(
                f"Adding a time lock of {settings.timelock_delta_seconds} seconds."
            )
            lock = (
                lock
                + ":"
                + str(
                    int(
                        (
                            datetime.now()
                            + timedelta(seconds=settings.timelock_delta_seconds)
                        ).timestamp()
                    )
                )
            )
            # we can also add some op_return data to the lock just for fun
            lock += ":rekt"

    await wallet.load_proofs()
    if split:
        await wallet.load_mint()
        _, send_proofs = await wallet.split_to_send(
            wallet.proofs, amount, lock, set_reserved=True
        )
    else:
        # get a proof with specific amount
        send_proofs = []
        for p in wallet.proofs:
            if not p.reserved and p.amount == amount:
                send_proofs = [p]
                break
        assert send_proofs, Exception(
            f"No proof with this amount found. Available amounts: {set([p.amount for p in wallet.proofs])}"
        )
        await wallet.set_reserved(send_proofs, reserved=True)

    token = await wallet.serialize_proofs(
        send_proofs,
        include_mints=True,
    )
    print(token)

    if legacy:
        print("")
        print("Old token format:")
        print("")
        token = await wallet.serialize_proofs(
            send_proofs,
            legacy=True,
        )
        print(token)

    wallet.status()
    return wallet.available_balance, token
