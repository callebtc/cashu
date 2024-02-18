# type: ignore
import asyncio
import json
import math
from typing import Dict, Optional

import bolt11
import httpx
from bolt11 import (
    decode,
)
from loguru import logger

from ..core.base import Amount, MeltQuote, Unit
from ..core.settings import settings
from .base import (
    InvoiceResponse,
    LightningBackend,
    PaymentQuoteResponse,
    PaymentResponse,
    PaymentStatus,
    StatusResponse,
)

# according to https://github.com/GaloyMoney/galoy/blob/7e79cc27304de9b9c2e7d7f4fdd3bac09df23aac/core/api/src/domain/bitcoin/index.ts#L59
BLINK_MAX_FEE_PERCENT = 0.5


class BlinkWallet(LightningBackend):
    """https://dev.blink.sv/
    Create API Key at: https://dashboard.blink.sv/
    """

    units = set([Unit.sat, Unit.usd])
    wallet_ids: Dict[Unit, str] = {}
    endpoint = "https://api.blink.sv/graphql"
    invoice_statuses = {"PENDING": None, "PAID": True, "EXPIRED": False}
    payment_execution_statuses = {"SUCCESS": True, "ALREADY_PAID": None}
    payment_statuses = {"SUCCESS": True, "PENDING": None, "FAILURE": False}

    def __init__(self):
        assert settings.mint_blink_key, "MINT_BLINK_KEY not set"
        self.client = httpx.AsyncClient(
            verify=not settings.debug,
            headers={
                "X-Api-Key": settings.mint_blink_key,
                "Content-Type": "application/json",
            },
            base_url=self.endpoint,
            timeout=15,
        )

    async def status(self) -> StatusResponse:
        try:
            r = await self.client.post(
                url=self.endpoint,
                data=('{"query":"query me { me { defaultAccount { wallets { id' ' walletCurrency balance }}}}", "variables":{}}'),
            )
            r.raise_for_status()
        except Exception as exc:
            logger.error(f"Blink API error: {str(exc)}")
            return StatusResponse(
                error_message=f"Failed to connect to {self.endpoint} due to: {exc}",
                balance=0,
            )

        try:
            resp: dict = r.json()
        except Exception:
            return StatusResponse(
                error_message=(f"Received invalid response from {self.endpoint}: {r.text}"),
                balance=0,
            )

        balance = 0
        for wallet_dict in resp["data"]["me"]["defaultAccount"]["wallets"]:
            if wallet_dict["walletCurrency"] == "USD":
                self.wallet_ids[Unit.usd] = wallet_dict["id"]
            elif wallet_dict["walletCurrency"] == "BTC":
                self.wallet_ids[Unit.sat] = wallet_dict["id"]
                balance = wallet_dict["balance"]

        return StatusResponse(error_message=None, balance=balance)

    async def create_invoice(
        self,
        amount: Amount,
        memo: Optional[str] = None,
        description_hash: Optional[bytes] = None,
        unhashed_description: Optional[bytes] = None,
    ) -> InvoiceResponse:
        self.assert_unit_supported(amount.unit)

        variables = {
            "input": {
                "amount": str(amount.to(Unit.sat).amount),
                "recipientWalletId": self.wallet_ids[Unit.sat],
            }
        }
        if description_hash:
            variables["input"]["descriptionHash"] = description_hash.hex()
        if memo:
            variables["input"]["memo"] = memo

        data = {
            "query": """
            mutation LnInvoiceCreateOnBehalfOfRecipient($input: LnInvoiceCreateOnBehalfOfRecipientInput!) {
                lnInvoiceCreateOnBehalfOfRecipient(input: $input) {
                    invoice {
                        paymentRequest
                        paymentHash
                        paymentSecret
                        satoshis
                    }
                    errors {
                        message path code
                    }
                }
            }
            """,
            "variables": variables,
        }
        try:
            r = await self.client.post(
                url=self.endpoint,
                data=json.dumps(data),
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Blink API error: {str(e)}")
            return InvoiceResponse(ok=False, error_message=str(e))

        resp = r.json()
        assert resp, "invalid response"
        payment_request = resp["data"]["lnInvoiceCreateOnBehalfOfRecipient"]["invoice"]["paymentRequest"]
        checking_id = payment_request

        return InvoiceResponse(
            ok=True,
            checking_id=checking_id,
            payment_request=payment_request,
        )

    async def pay_invoice(self, quote: MeltQuote, fee_limit_msat: int) -> PaymentResponse:
        variables = {
            "input": {
                "paymentRequest": quote.request,
                "walletId": self.wallet_ids[Unit.sat],
            }
        }
        data = {
            "query": """
            mutation lnInvoicePaymentSend($input: LnInvoicePaymentInput!) {
                lnInvoicePaymentSend(input: $input) {
                    errors {
                        message path code
                    }
                    status
                    transaction {
                        settlementAmount settlementFee status
                    }
                }
            }
            """,
            "variables": variables,
        }

        try:
            r = await self.client.post(
                url=self.endpoint,
                data=json.dumps(data),
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Blink API error: {str(e)}")
            return PaymentResponse(ok=False, error_message=str(e))

        resp: dict = r.json()
        paid = self.payment_execution_statuses[resp["data"]["lnInvoicePaymentSend"]["status"]]
        fee = resp["data"]["lnInvoicePaymentSend"]["transaction"]["settlementFee"]
        checking_id = quote.request

        return PaymentResponse(
            ok=paid,
            checking_id=checking_id,
            fee=Amount(Unit.sat, fee),
            preimage=None,
            error_message="Invoice already paid." if paid is None else None,
        )

    async def get_invoice_status(self, checking_id: str) -> PaymentStatus:
        variables = {"input": {"paymentRequest": checking_id}}
        data = {
            "query": """
        query lnInvoicePaymentStatus($input: LnInvoicePaymentStatusInput!) {
                lnInvoicePaymentStatus(input: $input) {
                    errors {
                        message path code
                    }
                    status
                }
            }
        """,
            "variables": variables,
        }
        try:
            r = await self.client.post(url=self.endpoint, data=json.dumps(data))
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Blink API error: {str(e)}")
            return PaymentStatus(paid=None)
        resp: dict = r.json()
        if resp["data"]["lnInvoicePaymentStatus"]["errors"]:
            logger.error("Blink Error", resp["data"]["lnInvoicePaymentStatus"]["errors"])
            return PaymentStatus(paid=None)
        paid = self.invoice_statuses[resp["data"]["lnInvoicePaymentStatus"]["status"]]
        return PaymentStatus(paid=paid)

    async def get_payment_status(self, checking_id: str) -> PaymentStatus:
        # Checking ID is the payment request and blink wants the payment hash
        payment_hash = bolt11.decode(checking_id).payment_hash
        variables = {
            "paymentHash": payment_hash,
            "walletId": self.wallet_ids[Unit.sat],
        }
        data = {
            "query": """
            query TransactionsByPaymentHash($paymentHash: PaymentHash!, $walletId: WalletId!) {
                me {
                    defaultAccount {
                        walletById(walletId: $walletId) {
                            transactionsByPaymentHash(paymentHash: $paymentHash) {
                                status
                                direction
                                settlementFee
                            }
                        }
                    }
                }
            }
            """,
            "variables": variables,
        }

        try:
            r = await self.client.post(
                url=self.endpoint,
                data=json.dumps(data),
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Blink API error: {str(e)}")
            return PaymentResponse(ok=False, error_message=str(e))

        resp: dict = r.json()
        # no result found
        if not resp["data"]["me"]["defaultAccount"]["walletById"]["transactionsByPaymentHash"]:
            return PaymentStatus(paid=None)

        paid = self.payment_statuses[resp["data"]["me"]["defaultAccount"]["walletById"]["transactionsByPaymentHash"][0]["status"]]
        fee = resp["data"]["me"]["defaultAccount"]["walletById"]["transactionsByPaymentHash"][0]["settlementFee"]

        return PaymentStatus(
            paid=paid,
            fee=Amount(Unit.sat, fee),
            preimage=None,
        )

    async def get_payment_quote(self, bolt11: str) -> PaymentQuoteResponse:
        variables = {
            "input": {
                "paymentRequest": bolt11,
                "walletId": self.wallet_ids[Unit.sat],
            }
        }
        data = {
            "query": """
            mutation lnInvoiceFeeProbe($input: LnInvoiceFeeProbeInput!) {
                lnInvoiceFeeProbe(input: $input) {
                    amount
                    errors {
                        message path code
                    }
                }
            }
            """,
            "variables": variables,
        }

        try:
            r = await self.client.post(
                url=self.endpoint,
                data=json.dumps(data),
            )
            r.raise_for_status()
        except Exception as e:
            logger.error(f"Blink API error: {str(e)}")
            return PaymentResponse(ok=False, error_message=str(e))
        resp: dict = r.json()

        invoice_obj = decode(bolt11)
        assert invoice_obj.amount_msat, "invoice has no amount."

        amount_msat = int(invoice_obj.amount_msat)

        fees_response_msat = int(resp["data"]["lnInvoiceFeeProbe"]["amount"]) * 1000
        # we either take fee_msat_response or the BLINK_MAX_FEE_PERCENT, whichever is higher
        fees_msat = max(fees_response_msat, math.ceil(amount_msat / 100 * BLINK_MAX_FEE_PERCENT))

        fees = Amount(unit=Unit.msat, amount=fees_msat)
        amount = Amount(unit=Unit.msat, amount=amount_msat)
        return PaymentQuoteResponse(checking_id=bolt11, fee=fees, amount=amount)


async def main():
    pass


if __name__ == "__main__":
    asyncio.run(main())
