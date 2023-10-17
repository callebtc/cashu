from typing import Literal, Optional, Tuple, Union

from loguru import logger

from ..core.base import (
    Invoice,
)
from ..core.db import Connection, Database
from ..core.errors import (
    InvoiceNotPaidError,
    LightningError,
)
from ..lightning.base import Wallet
from ..mint.crud import LedgerCrud
from .protocols import SupportLightning, SupportsDb


class LedgerLightning(SupportLightning, SupportsDb):
    """Lightning functions for the ledger."""

    lightning: Wallet
    crud: LedgerCrud
    db: Database

    async def _request_lightning_invoice(self, amount: int) -> Tuple[str, str]:
        """Generate a Lightning invoice using the funding source backend.

        Args:
            amount (int): Amount of invoice (in Satoshis)

        Raises:
            Exception: Error with funding source.

        Returns:
            Tuple[str, str]: Bolt11 invoice and payment id (for lookup)
        """
        logger.trace(
            "_request_lightning_invoice: Requesting Lightning invoice for"
            f" {amount} satoshis."
        )
        error, balance = await self.lightning.status()
        logger.trace(f"_request_lightning_invoice: Lightning wallet balance: {balance}")
        if error:
            raise LightningError(f"Lightning wallet not responding: {error}")
        (
            ok,
            checking_id,
            payment_request,
            error_message,
        ) = await self.lightning.create_invoice(amount, "Cashu deposit")
        logger.trace(
            f"_request_lightning_invoice: Lightning invoice: {payment_request}"
        )

        if not ok:
            raise LightningError(f"Lightning wallet error: {error_message}")
        assert payment_request and checking_id, LightningError(
            "could not fetch invoice from Lightning backend"
        )
        return payment_request, checking_id

    async def _check_lightning_invoice(
        self, *, amount: int, id: str, conn: Optional[Connection] = None
    ) -> Literal[True]:
        """Checks with the Lightning backend whether an invoice with `id` was paid.

        Args:
            amount (int): Amount of the outputs the wallet wants in return (in Satoshis).
            id (str): Id to look up Lightning invoice by.

        Raises:
            Exception: Invoice not found.
            Exception: Tokens for invoice already issued.
            Exception: Amount larger than invoice amount.
            Exception: Invoice not paid yet
            e: Update database and pass through error.

        Returns:
            bool: True if invoice has been paid, else False
        """
        invoice: Union[Invoice, None] = await self.crud.get_lightning_invoice(
            id=id, db=self.db, conn=conn
        )
        if invoice is None:
            raise LightningError("invoice not found.")
        if invoice.issued:
            raise LightningError("tokens already issued for this invoice.")
        if amount > invoice.amount:
            raise LightningError(
                f"requested amount too high: {amount}. Invoice amount: {invoice.amount}"
            )
        assert invoice.payment_hash, "invoice has no payment hash."
        # set this invoice as issued
        await self.crud.update_lightning_invoice(
            id=id, issued=True, db=self.db, conn=conn
        )

        try:
            status = await self.lightning.get_invoice_status(invoice.payment_hash)
            if status.paid:
                return status.paid
            else:
                raise InvoiceNotPaidError()
        except Exception as e:
            # unset issued
            await self.crud.update_lightning_invoice(
                id=id, issued=False, db=self.db, conn=conn
            )
            raise e

    async def _pay_lightning_invoice(self, invoice: str, fee_limit_msat: int):
        """Pays a Lightning invoice via the funding source backend.

        Args:
            invoice (str): Bolt11 Lightning invoice
            fee_limit_msat (int): Maximum fee reserve for payment (in Millisatoshi)

        Raises:
            Exception: Funding source error.

        Returns:
            Tuple[bool, string, int]: Returns payment status, preimage of invoice, paid fees (in Millisatoshi)
        """
        error, balance = await self.lightning.status()
        if error:
            raise LightningError(f"Lightning wallet not responding: {error}")
        (
            ok,
            checking_id,
            fee_msat,
            preimage,
            error_message,
        ) = await self.lightning.pay_invoice(invoice, fee_limit_msat=fee_limit_msat)
        logger.trace(f"_pay_lightning_invoice: Lightning payment status: {ok}")
        # make sure that fee is positive
        fee_msat = abs(fee_msat) if fee_msat else fee_msat
        return ok, preimage, fee_msat
