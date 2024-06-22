from typing import List, Optional, Union

from pydantic import BaseModel, Field

from ..core.base import (
    Proof,
)
from ..core.settings import settings


class GatewayMint(BaseModel):
    mint: str


class GatewayInfo(BaseModel):
    mints: List[GatewayMint]


class GatewayMintQuoteRequest(BaseModel):
    unit: str = Field(..., max_length=settings.mint_max_request_length)  # output unit
    amount: int = Field(..., gt=0)  # output amount
    payment_hash: str = Field(
        ..., max_length=settings.mint_max_request_length
    )  # payment hash
    mint: str = Field(..., max_length=settings.mint_max_request_length)  # mint url


class GatewayMintQuoteResponse(BaseModel):
    quote: str  # quote id
    request: str  # input payment request
    paid: bool  # whether the request has been paid
    expiry: Optional[int]  # expiry of the quote


class GatewayMintRequest(BaseModel):
    quote: str = Field(..., max_length=settings.mint_max_request_length)  # quote id


class GatewayMintResponse(BaseModel):
    inputs: List[Proof] = Field(..., max_items=settings.mint_max_request_length)


class GatewayMeltQuoteRequest(BaseModel):
    unit: str = Field(..., max_length=settings.mint_max_request_length)  # input unit
    request: str = Field(
        ..., max_length=settings.mint_max_request_length
    )  # output payment request
    mint: str = Field(..., max_length=settings.mint_max_request_length)  # mint url


class GatewayMeltQuoteResponse(BaseModel):
    quote: str  # quote id
    pubkey: str  # P2PK pubkey of the gateway
    amount: int  # input amount
    expiry: int  # expiry of the quote
    paid: bool  # whether the quote has been paid


class GatewayMeltRequest(BaseModel):
    quote: str = Field(..., max_length=settings.mint_max_request_length)  # quote id
    inputs: List[Proof] = Field(..., max_items=settings.mint_max_request_length)


class GatewayMeltResponse(BaseModel):
    paid: Union[bool, None]
    payment_preimage: Union[str, None]
