from typing import Union

from fastapi import APIRouter, Request
from loguru import logger

from ..core.base import (
    CheckFeesRequest,
    CheckFeesResponse,
    CheckSpendableRequest,
    CheckSpendableResponse,
    GetInfoResponse,
    KeysetsResponse,
    KeysetsResponseKeyset,
    KeysResponse,
    KeysResponseKeyset,
    PostMeltQuoteRequest,
    PostMeltQuoteResponse,
    PostMeltRequest,
    PostMeltResponse,
    PostMintQuoteRequest,
    PostMintQuoteResponse,
    PostMintRequest,
    PostMintResponse,
    PostRestoreResponse,
    PostSplitRequest,
    PostSplitResponse,
    PostSplitResponse_Deprecated,
)
from ..core.errors import CashuError
from ..core.settings import settings
from ..mint.startup import ledger

router: APIRouter = APIRouter()


@router.get(
    "/info",
    name="Mint information",
    summary="Mint information, operator contact information, and other info.",
    response_model=GetInfoResponse,
    response_model_exclude_none=True,
)
async def info() -> GetInfoResponse:
    logger.trace("> GET /info")
    return GetInfoResponse(
        name=settings.mint_info_name,
        pubkey=ledger.pubkey.serialize().hex() if ledger.pubkey else None,
        version=f"Nutshell/{settings.version}",
        description=settings.mint_info_description,
        description_long=settings.mint_info_description_long,
        contact=settings.mint_info_contact,
        nuts=settings.mint_info_nuts,
        motd=settings.mint_info_motd,
        parameter={
            "max_peg_in": settings.mint_max_peg_in,
            "max_peg_out": settings.mint_max_peg_out,
            "peg_out_only": settings.mint_peg_out_only,
        },
    )


@router.get(
    "/v1/keys",
    name="Mint public keys",
    summary="Get the public keys of the newest mint keyset",
    response_description=(
        "A dictionary of all supported token values of the mint and their associated"
        " public key of the current keyset."
    ),
    response_model=KeysResponse,
)
async def keys():
    """This endpoint returns a dictionary of all supported token values of the mint and their associated public key."""
    logger.trace("> GET /keys")
    keyset = ledger.keyset
    keyset_for_response = KeysResponseKeyset(
        id=keyset.id,
        symbol=keyset.symbol,
        keys={str(k): v for k, v in keyset.public_keys_hex.items()},
    )
    return KeysResponse(keysets=[keyset_for_response])


@router.get(
    "/v1/keys/{keyset_id}",
    name="Keyset public keys",
    summary="Public keys of a specific keyset",
    response_description=(
        "A dictionary of all supported token values of the mint and their associated"
        " public key for a specific keyset."
    ),
    response_model=KeysResponse,
)
async def keyset_keys(keyset_id: str, request: Request):
    """
    Get the public keys of the mint from a specific keyset id.
    """
    logger.trace(f"> GET /keys/{keyset_id}")
    # BEGIN BACKWARDS COMPATIBILITY < 0.14.0
    # if keyset_id is not hex, we assume it is base64 and sanitize it
    try:
        int(keyset_id, 16)
    except ValueError:
        keyset_id = keyset_id.replace("-", "+").replace("_", "/")
    # END BACKWARDS COMPATIBILITY < 0.14.0

    keyset = ledger.keysets.keysets.get(keyset_id)
    if keyset is None:
        raise CashuError(code=0, detail="Keyset not found.")

    keyset_for_response = KeysResponseKeyset(
        id=keyset.id,
        symbol=keyset.symbol,
        keys={str(k): v for k, v in keyset.public_keys_hex.items()},
    )
    return KeysResponse(keysets=[keyset_for_response])


@router.get(
    "/v1/keysets",
    name="Active keysets",
    summary="Get all active keyset id of the mind",
    response_model=KeysetsResponse,
    response_description="A list of all active keyset ids of the mint.",
)
async def keysets() -> KeysetsResponse:
    """This endpoint returns a list of keysets that the mint currently supports and will accept tokens from."""
    logger.trace("> GET /keysets")
    keysets = []
    for id, keyset in ledger.keysets.keysets.items():
        keysets.append(KeysetsResponseKeyset(id=id, symbol=keyset.symbol, active=True))
    return KeysetsResponse(keysets=keysets)


@router.post(
    "/v1/mint/quote",
    name="Request mint quote",
    summary="Request a quote for minting of new tokens",
    response_model=PostMintQuoteResponse,
    response_description="A payment request to mint tokens of a denomination",
)
async def mint_quote(payload: PostMintQuoteRequest) -> PostMintQuoteResponse:
    """
    Request minting of new tokens. The mint responds with a Lightning invoice.
    This endpoint can be used for a Lightning invoice UX flow.

    Call `POST /mint` after paying the invoice.
    """
    logger.trace(f"> POST /v1/mint: payload={payload}")
    amount = payload.amount
    if amount > 21_000_000 * 100_000_000 or amount <= 0:
        raise CashuError(code=0, detail="Amount must be a valid amount of sat.")
    if settings.mint_peg_out_only:
        raise CashuError(code=0, detail="Mint does not allow minting new tokens.")

    payment_request, quote = await ledger.mint_quote(amount)
    resp = PostMintQuoteResponse(
        request=payment_request,
        quote=quote,
        method="bolt11",
        symbol="sat",
        amount=amount,
    )
    logger.trace(f"< GET /mint: {resp}")
    return resp


@router.post(
    "/v1/mint",
    name="Mint tokens",
    summary="Mint tokens in exchange for a Bitcoin payment that the user has made",
    response_model=PostMintResponse,
    response_description=(
        "A list of blinded signatures that can be used to create proofs."
    ),
)
async def mint(
    payload: PostMintRequest,
) -> PostMintResponse:
    """
    Requests the minting of tokens belonging to a paid payment request.

    Call this endpoint after `GET /mint`.
    """
    logger.trace(f"> POST /mint: {payload}")

    promises = await ledger.mint(outputs=payload.outputs, quote=payload.quote)
    blinded_signatures = PostMintResponse(quote=payload.quote, signatures=promises)
    logger.trace(f"< POST /mint: {blinded_signatures}")
    return blinded_signatures


@router.post(
    "/v1/melt/quote",
    summary="Request a quote for melting tokens",
    response_model=PostMeltQuoteResponse,
    response_description="Melt tokens for a payment on a supported payment method.",
)
async def melt_quote(payload: PostMeltQuoteRequest) -> PostMeltQuoteResponse:
    """
    Request a quote for melting tokens.
    """
    logger.trace(f"> POST /melt/quote: {payload}")
    quote = await ledger.melt_quote(payload.request)  # TODO
    logger.trace(f"< POST /melt/quote: {quote}")
    return quote


@router.post(
    "/v1/melt",
    name="Melt tokens",
    summary=(
        "Melt tokens for a Bitcoin payment that the mint will make for the user in"
        " exchange"
    ),
    response_model=PostMeltResponse,
    response_description=(
        "The state of the payment, a preimage as proof of payment, and a list of"
        " promises for change."
    ),
)
async def melt(payload: PostMeltRequest) -> PostMeltResponse:
    """
    Requests tokens to be destroyed and sent out via Lightning.
    """
    logger.trace(f"> POST /melt: {payload}")
    ok, preimage, change_promises = await ledger.melt(
        payload.inputs, payload.quote, payload.outputs
    )
    resp = PostMeltResponse(
        quote="to_be_replaced", paid=ok, proof=preimage, change=change_promises
    )
    logger.trace(f"< POST /melt: {resp}")
    return resp


@router.post(
    "/check",
    name="Check proof state",
    summary="Check whether a proof is spent already or is pending in a transaction",
    response_model=CheckSpendableResponse,
    response_description=(
        "Two lists of booleans indicating whether the provided proofs "
        "are spendable or pending in a transaction respectively."
    ),
)
async def check_spendable(
    payload: CheckSpendableRequest,
) -> CheckSpendableResponse:
    """Check whether a secret has been spent already or not."""
    logger.trace(f"> POST /check: {payload}")
    spendableList, pendingList = await ledger.check_proof_state(payload.proofs)
    logger.trace(f"< POST /check <spendable>: {spendableList}")
    logger.trace(f"< POST /check <pending>: {pendingList}")
    return CheckSpendableResponse(spendable=spendableList, pending=pendingList)


@router.post(
    "/checkfees",
    name="Check fees",
    summary="Check fee reserve for a Lightning payment",
    response_model=CheckFeesResponse,
    response_description="The fees necessary to pay a Lightning invoice.",
)
async def check_fees(payload: CheckFeesRequest) -> CheckFeesResponse:
    """
    Responds with the fees necessary to pay a Lightning invoice.
    Used by wallets for figuring out the fees they need to supply together with the payment amount.
    This is can be useful for checking whether an invoice is internal (Cashu-to-Cashu).
    """
    logger.trace(f"> POST /checkfees: {payload}")
    fees_sat = await ledger.get_melt_fees(payload.pr)
    logger.trace(f"< POST /checkfees: {fees_sat}")
    return CheckFeesResponse(fee=fees_sat)


@router.post(
    "/split",
    name="Split",
    summary="Split proofs at a specified amount",
    response_model=Union[PostSplitResponse, PostSplitResponse_Deprecated],
    response_description=(
        "A list of blinded signatures that can be used to create proofs."
    ),
)
async def split(
    payload: PostSplitRequest,
) -> Union[PostSplitResponse, PostSplitResponse_Deprecated]:
    """
    Requests a set of Proofs to be split into two a new set of BlindedSignatures.

    This endpoint is used by Alice to split a set of proofs before making a payment to Carol.
    It is then used by Carol (by setting split=total) to redeem the tokens.
    """
    logger.trace(f"> POST /split: {payload}")
    assert payload.outputs, Exception("no outputs provided.")

    signatures = await ledger.split(proofs=payload.inputs, outputs=payload.outputs)

    return PostSplitResponse(signatures=signatures)


@router.post(
    "/restore",
    name="Restore",
    summary="Restores a blinded signature from a secret",
    response_model=PostRestoreResponse,
    response_description=(
        "Two lists with the first being the list of the provided outputs that "
        "have an associated blinded signature which is given in the second list."
    ),
)
async def restore(payload: PostMintRequest) -> PostRestoreResponse:
    assert payload.outputs, Exception("no outputs provided.")
    outputs, promises = await ledger.restore(payload.outputs)
    return PostRestoreResponse(outputs=outputs, promises=promises)
