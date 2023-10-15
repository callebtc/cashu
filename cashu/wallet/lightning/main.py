import asyncio

import bolt11

from cashu.wallet.lightning import LightningWallet


async def main():
    # wallet = LightningWallet("http://localhost:3338", "data/lightning.db")
    # await wallet.async_init("http://localhost:3338", "data/lightning.db")
    wallet = await LightningWallet().with_db(
        url="http://localhost:3338", db="data/lightning.db"
    )
    await wallet.async_init()
    invoice = await wallet.create_invoice(1000)

    print(invoice)
    # return
    assert invoice.payment_hash
    print("balance", await wallet.get_balance())
    state = ""
    while not state.startswith("paid"):
        print("checking invoice state")
        state = await wallet.get_invoice_status(invoice.payment_hash)
        await asyncio.sleep(1)
        print("state:", state)

    print("balance", await wallet.get_balance())

    invoice2 = await wallet.create_invoice(10)
    pr = invoice2.bolt11
    invoice_obj = bolt11.decode(pr)
    print("paying invoice", pr)

    asyncio.create_task(wallet.pay_invoice(pr=pr))

    state = ""
    while not state.startswith("paid"):
        state = await wallet.get_payment_status(invoice_obj.payment_hash)
        print("state", state)
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
