from syncer import sync
import aiohttp

from model.ledger_transaction import LedgerTransaction

base_url = "https://neoscan.io"
last_transactions_uri = "/api/main_net/v1/get_last_transactions_by_address/{address}/{page}"
get_transaction_uri = "/api/main_net/v1/get_transaction/"


@sync
async def get_transaction_from_ledger(tx_id, timeout=25) -> LedgerTransaction:
    timeout = aiohttp.ClientTimeout(timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        resp = await session.request(method="get", url=base_url + get_transaction_uri + tx_id)
        resp_json = await resp.json()
        return LedgerTransaction(
            txId=resp_json.get("txid"),
            ins=[
                in_address.get("address_hash")
                for in_address in resp_json.get("vin")
            ],
            outs=[
                in_address.get("address_hash")
                for in_address in resp_json.get("vouts")
            ]
        )


@sync
async def get_addresses_from_xpub(x_pub: str, timeout=25):
    addresses = [x_pub]
    return addresses
