from syncer import sync
import aiohttp

from model.ledger_transaction import LedgerTransaction

base_url = "https://neoscan.io"
last_transactions_uri = "/api/main_net/v1/get_last_transactions_by_address/{address}/{page}"
get_transaction_uri = "/api/main_net/v1/get_transaction/"


def get_model_from_api(resp_json):
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
async def get_transaction_from_ledger(tx_id, timeout=25) -> LedgerTransaction:
    timeout = aiohttp.ClientTimeout(timeout)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        resp = await session.request(method="get", url=base_url + get_transaction_uri + tx_id)
        resp_json = await resp.json()
        return get_model_from_api(resp_json)


@sync
async def get_addresses_from_xpub(x_pub: str, timeout=25):
#    timeout = aiohttp.ClientTimeout(timeout)
    addresses = [x_pub]

#    async with aiohttp.ClientSession(timeout=timeout) as session:
#        resp = await session.request(method="get", url=base_url + x_pub)
#        resp_json = await resp.json()
#        for transaction in resp_json.get("txs"):
#            for transaction_input in transaction.get("inputs"):
#                if "xpub" in transaction_input.get("prev_out") and not transaction_input.get("prev_out").get("addr") in addresses:
#                    addresses.append(transaction_input.get("prev_out").get("addr"))
#            for transaction_output in transaction.get("out"):
#                if "xpub" in transaction_output and not transaction_output.get("addr") in addresses:
#                    addresses.append(transaction_output.get("addr"))
#            pass
    return addresses
