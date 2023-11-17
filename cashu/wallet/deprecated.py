from posixpath import join
from typing import List, Optional, Tuple, Union

import httpx
from httpx import Response
from loguru import logger

from ..core.base import (
    BlindedMessage,
    BlindedSignature,
    GetMintResponse_deprecated,
    Invoice,
    KeysetsResponse_deprecated,
    PostMeltRequest_deprecated,
    PostMeltResponse_deprecated,
    PostMintRequest_deprecated,
    PostMintResponse_deprecated,
    PostRestoreResponse,
    PostSplitRequest_Deprecated,
    PostSplitResponse_Deprecated,
    Proof,
    WalletKeyset,
)
from ..core.crypto.secp import PublicKey
from ..core.settings import settings
from ..tor.tor import TorProxy
from .protocols import SupportsHttpxClient, SupportsMintURL


def async_set_httpx_client(func):
    """
    Decorator that wraps around any async class method of LedgerAPI that makes
    API calls. Sets some HTTP headers and starts a Tor instance if none is
    already running and and sets local proxy to use it.
    """

    async def wrapper(self, *args, **kwargs):
        # set proxy
        proxies_dict = {}
        proxy_url: Union[str, None] = None
        if settings.tor and TorProxy().check_platform():
            self.tor = TorProxy(timeout=True)
            self.tor.run_daemon(verbose=True)
            proxy_url = "socks5://localhost:9050"
        elif settings.socks_proxy:
            proxy_url = f"socks5://{settings.socks_proxy}"
        elif settings.http_proxy:
            proxy_url = settings.http_proxy
        if proxy_url:
            proxies_dict.update({"all://": proxy_url})

        headers_dict = {"Client-version": settings.version}

        self.httpx = httpx.AsyncClient(
            verify=not settings.debug,
            proxies=proxies_dict,  # type: ignore
            headers=headers_dict,
            base_url=self.url,
        )
        return await func(self, *args, **kwargs)

    return wrapper


class LedgerAPIDeprecated(SupportsHttpxClient, SupportsMintURL):
    """Deprecated wallet class, will be removed in the future."""

    httpx: httpx.AsyncClient
    url: str

    @staticmethod
    def raise_on_error(
        resp: Response,
    ) -> None:
        """Raises an exception if the response from the mint contains an error.

        Args:
            resp_dict (Response): Response dict (previously JSON) from mint

        Raises:
            Exception: if the response contains an error
        """
        resp_dict = resp.json()
        if "detail" in resp_dict:
            logger.trace(f"Error from mint: {resp_dict}")
            error_message = f"Mint Error: {resp_dict['detail']}"
            if "code" in resp_dict:
                error_message += f" (Code: {resp_dict['code']})"
            raise Exception(error_message)
        # raise for status if no error
        resp.raise_for_status()

    @async_set_httpx_client
    async def _get_keys_deprecated(self, url: str) -> WalletKeyset:
        """API that gets the current keys of the mint

        Args:
            url (str): Mint URL

        Returns:
            WalletKeyset: Current mint keyset

        Raises:
            Exception: If no keys are received from the mint
        """
        logger.warning(f"Using deprecated API call: {url}/keys")
        resp = await self.httpx.get(
            url + "/keys",
        )
        self.raise_on_error(resp)
        keys: dict = resp.json()
        assert len(keys), Exception("did not receive any keys")
        keyset_keys = {
            int(amt): PublicKey(bytes.fromhex(val), raw=True)
            for amt, val in keys.items()
        }
        keyset = WalletKeyset(
            public_keys=keyset_keys, mint_url=url, use_deprecated_id=True
        )
        return keyset

    @async_set_httpx_client
    async def _get_keys_of_keyset_deprecated(
        self, url: str, keyset_id: str
    ) -> WalletKeyset:
        """API that gets the keys of a specific keyset from the mint.


        Args:
            url (str): Mint URL
            keyset_id (str): base64 keyset ID, needs to be urlsafe-encoded before sending to mint (done in this method)

        Returns:
            WalletKeyset: Keyset with ID keyset_id

        Raises:
            Exception: If no keys are received from the mint
        """
        logger.warning(f"Using deprecated API call: {url}/keys/{keyset_id}")
        keyset_id_urlsafe = keyset_id.replace("+", "-").replace("/", "_")
        resp = await self.httpx.get(
            url + f"/keys/{keyset_id_urlsafe}",
        )
        self.raise_on_error(resp)
        keys = resp.json()
        assert len(keys), Exception("did not receive any keys")
        keyset_keys = {
            int(amt): PublicKey(bytes.fromhex(val), raw=True)
            for amt, val in keys.items()
        }
        keyset = WalletKeyset(
            id=keyset_id, public_keys=keyset_keys, mint_url=url, use_deprecated_id=True
        )
        return keyset

    @async_set_httpx_client
    async def _get_keyset_ids_deprecated(self, url: str) -> List[str]:
        """API that gets a list of all active keysets of the mint.

        Args:
            url (str): Mint URL

        Returns:
            KeysetsResponse (List[str]): List of all active keyset IDs of the mint

        Raises:
            Exception: If no keysets are received from the mint
        """
        logger.warning(f"Using deprecated API call: {url}/keysets")
        resp = await self.httpx.get(
            url + "/keysets",
        )
        self.raise_on_error(resp)
        keysets_dict = resp.json()
        keysets = KeysetsResponse_deprecated.parse_obj(keysets_dict)
        assert len(keysets.keysets), Exception("did not receive any keysets")
        return keysets.keysets

    @async_set_httpx_client
    async def request_mint_deprecated(self, amount) -> Invoice:
        """Requests a mint from the server and returns Lightning invoice.

        Args:
            amount (int): Amount of tokens to mint

        Returns:
            Invoice: Lightning invoice

        Raises:
            Exception: If the mint request fails
        """
        logger.trace("Requesting mint: GET /mint")
        resp = await self.httpx.get(self.url + "/mint", params={"amount": amount})
        self.raise_on_error(resp)
        return_dict = resp.json()
        mint_response = GetMintResponse_deprecated.parse_obj(return_dict)
        return Invoice(amount=amount, bolt11=mint_response.pr, id=mint_response.hash)

    @async_set_httpx_client
    async def mint_deprecated(
        self, outputs: List[BlindedMessage], hash: Optional[str] = None
    ) -> List[BlindedSignature]:
        """Mints new coins and returns a proof of promise.

        Args:
            outputs (List[BlindedMessage]): Outputs to mint new tokens with
            hash (str, optional): Hash of the paid invoice. Defaults to None.

        Returns:
            list[Proof]: List of proofs.

        Raises:
            Exception: If the minting fails
        """
        outputs_payload = PostMintRequest_deprecated(outputs=outputs)
        logger.trace("Checking Lightning invoice. POST /mint")
        resp = await self.httpx.post(
            self.url + "/mint",
            json=outputs_payload.dict(),
            params={
                "hash": hash,
                "payment_hash": hash,  # backwards compatibility pre 0.12.0
            },
        )
        self.raise_on_error(resp)
        response_dict = resp.json()
        logger.trace("Lightning invoice checked. POST /mint")
        promises = PostMintResponse_deprecated.parse_obj(response_dict).promises
        return promises

    @async_set_httpx_client
    async def pay_lightning_deprecated(
        self, proofs: List[Proof], invoice: str, outputs: Optional[List[BlindedMessage]]
    ):
        """
        Accepts proofs and a lightning invoice to pay in exchange.
        """

        payload = PostMeltRequest_deprecated(proofs=proofs, pr=invoice, outputs=outputs)

        def _meltrequest_include_fields(proofs: List[Proof]):
            """strips away fields from the model that aren't necessary for the /melt"""
            proofs_include = {"id", "amount", "secret", "C", "script"}
            return {
                "proofs": {i: proofs_include for i in range(len(proofs))},
                "pr": ...,
                "outputs": ...,
            }

        resp = await self.httpx.post(
            self.url + "/melt",
            json=payload.dict(include=_meltrequest_include_fields(proofs)),  # type: ignore
        )
        self.raise_on_error(resp)
        return_dict = resp.json()

        return PostMeltResponse_deprecated.parse_obj(return_dict)

    @async_set_httpx_client
    async def restore_promises(
        self, outputs: List[BlindedMessage]
    ) -> Tuple[List[BlindedMessage], List[BlindedSignature]]:
        """
        Asks the mint to restore promises corresponding to outputs.
        """
        payload = PostMintRequest_deprecated(outputs=outputs)
        resp = await self.httpx.post(self.url + "/v1/restore", json=payload.dict())
        self.raise_on_error(resp)
        response_dict = resp.json()
        returnObj = PostRestoreResponse.parse_obj(response_dict)
        return returnObj.outputs, returnObj.promises

    @async_set_httpx_client
    async def split_deprecated(
        self,
        proofs: List[Proof],
        outputs: List[BlindedMessage],
    ) -> List[BlindedSignature]:
        """Consume proofs and create new promises based on amount split."""
        logger.debug("Calling split. POST /split")
        split_payload = PostSplitRequest_Deprecated(proofs=proofs, outputs=outputs)

        # construct payload
        def _splitrequest_include_fields(proofs: List[Proof]):
            """strips away fields from the model that aren't necessary for the /split"""
            proofs_include = {
                "id",
                "amount",
                "secret",
                "C",
                "witness",
            }
            return {
                "outputs": ...,
                "inputs": {i: proofs_include for i in range(len(proofs))},
            }

        resp = await self.httpx.post(
            join(self.url, "/split"),
            json=split_payload.dict(include=_splitrequest_include_fields(proofs)),  # type: ignore
        )
        self.raise_on_error(resp)
        promises_dict = resp.json()
        mint_response = PostSplitResponse_Deprecated.parse_obj(promises_dict)
        promises = [BlindedSignature(**p.dict()) for p in mint_response.promises]

        if len(promises) == 0:
            raise Exception("received no splits.")

        return promises
