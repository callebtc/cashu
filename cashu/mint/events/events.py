from loguru import logger

from ...core.base import MeltQuote, MintQuote, ProofState
from ...core.models import PostMeltQuoteResponse, PostMintQuoteResponse
from .client_manager import LedgerEventClientManager
from .ledger_event import LedgerEvent


class LedgerEventManager:
    """LedgerEventManager is a subscription service from the mint
    for client websockets that subscribe to event updates.

    Yields:
        _type_: Union[MintQuote, MeltQuote]
    """

    clients: list[LedgerEventClientManager] = []

    MAX_CLIENTS = 1000

    def add_client(self, client: LedgerEventClientManager) -> bool:
        if len(self.clients) >= self.MAX_CLIENTS:
            return False
        self.clients.append(client)
        logger.debug(f"Added websocket subscription client {client}")
        return True

    def remove_client(self, client: LedgerEventClientManager) -> None:
        self.clients.remove(client)

    def serialize_event(self, event: LedgerEvent) -> dict:
        if isinstance(event, MintQuote):
            return_dict = PostMintQuoteResponse.parse_obj(event.dict()).dict()
        elif isinstance(event, MeltQuote):
            return_dict = PostMeltQuoteResponse.parse_obj(event.dict()).dict()
        elif isinstance(event, ProofState):
            return_dict = event.dict(exclude_unset=True, exclude_none=True)
        return return_dict

    async def submit(self, event: LedgerEvent) -> None:
        if not isinstance(event, LedgerEvent):
            raise ValueError(f"Unsupported event object type {type(event)}")

        for client in self.clients:
            kind_sub = client.subscriptions.get(event.kind, {})
            for sub in kind_sub.get(event.identifier, []):
                logger.trace(
                    f"Submitting event to sub {sub}: {self.serialize_event(event)}"
                )
                await client._send_obj(self.serialize_event(event), subId=sub)
