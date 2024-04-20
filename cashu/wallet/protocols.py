from typing import Protocol

import httpx

from ..core.base import Unit
from ..core.crypto.secp import PrivateKey
from ..core.db import Database


class SupportsPrivateKey(Protocol):
    private_key: PrivateKey


class SupportsDb(Protocol):
    db: Database


class SupportsKeysets(Protocol):
    keyset_id: str


class SupportsUnit(Protocol):
    unit: Unit


class SupportsHttpxClient(Protocol):
    httpx: httpx.AsyncClient


class SupportsMintURL(Protocol):
    url: str
