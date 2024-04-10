import asyncio
from typing import Mapping

from loguru import logger

from ..core.base import Method, Unit
from ..core.db import Database
from ..lightning.base import LightningBackend
from ..mint.crud import LedgerCrud
from .events.events import LedgerEventManager
from .protocols import SupportsBackends, SupportsDb, SupportsEvents


class LedgerTasks(SupportsDb, SupportsBackends, SupportsEvents):
    backends: Mapping[Method, Mapping[Unit, LightningBackend]] = {}
    db: Database
    crud: LedgerCrud
    events: LedgerEventManager

    async def dispatch_listeners(self) -> None:
        for method, unitbackends in self.backends.items():
            for unit, backend in unitbackends.items():
                logger.debug(
                    f"Dispatching backend invoice listener for {method} {unit} {backend.__class__.__name__}"
                )
                asyncio.create_task(self.invoice_listener(backend))

    async def invoice_listener(self, backend: LightningBackend) -> None:
        async for checking_id in backend.paid_invoices_stream():
            await self.invoice_callback_dispatcher(checking_id)

    async def invoice_callback_dispatcher(self, checking_id: str) -> None:
        logger.success(f"invoice callback dispatcher: {checking_id}")
        quote = await self.crud.get_mint_quote(checking_id=checking_id, db=self.db)
        if not quote:
            logger.error(f"Quote not found for {checking_id}")
            return
        await self.events.submit(quote)
