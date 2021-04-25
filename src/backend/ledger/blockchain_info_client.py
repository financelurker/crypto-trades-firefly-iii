from syncer import sync
import aiohttp

from model.ledger_transaction import LedgerTransaction

base_url = "https://blockchain.info"
address_uri = "/multiaddr?active="
transaction_uri = "/rawtx/"


@sync
async def get_transaction_from_ledger(tx_id, timeout=25) -> LedgerTransaction:
    timeout = aiohttp.ClientTimeout(timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        resp = await session.request(method="get", url=base_url + transaction_uri + tx_id)
        resp_json = await resp.json()
        return LedgerTransaction(
            txId=tx_id,
            ins=[
                address.get("prev_out").get("addr") for address in resp_json.get("inputs")
            ],
            outs=[
                address.get("addr") for address in resp_json.get("out")
            ]
        )


@sync
async def get_addresses_from_xpub(x_pub: str, timeout=25):
    timeout = aiohttp.ClientTimeout(timeout)
    addresses = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        page = 0
        page_size = 50
        load_next = True
        while load_next:
            resp = await session.request(method="get", url=base_url + address_uri + x_pub + "&n=" + str(page_size) + "&offset=" + str(page_size * page))
            resp_json = await resp.json()
            new_transactions = resp_json.get("txs")
            for transaction in new_transactions:
                for transaction_input in transaction.get("inputs"):
                    if "xpub" in transaction_input.get("prev_out") and not transaction_input.get("prev_out").get(
                            "addr") in addresses:
                        addresses.append(transaction_input.get("prev_out").get("addr"))
                for transaction_output in transaction.get("out"):
                    if "xpub" in transaction_output and not transaction_output.get("addr") in addresses:
                        addresses.append(transaction_output.get("addr"))
            if len(new_transactions) < page_size:
                load_next = False
            else:
                page += 1

    return addresses
