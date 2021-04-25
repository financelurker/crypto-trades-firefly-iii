from syncer import sync
import aiohttp

base_url = "https://blockchain.info/multiaddr?active="


@sync
async def get_addresses_from_xpub(x_pub: str, timeout=25):
    timeout = aiohttp.ClientTimeout(timeout)
    addresses = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        resp = await session.request(method="get", url=base_url + x_pub)
        resp_json = await resp.json()
        for transaction in resp_json.get("txs"):
            for transaction_input in transaction.get("inputs"):
                if "xpub" in transaction_input.get("prev_out") and not transaction_input.get("prev_out").get("addr") in addresses:
                    addresses.append(transaction_input.get("prev_out").get("addr"))
            for transaction_output in transaction.get("out"):
                if "xpub" in transaction_output and not transaction_output.get("addr") in addresses:
                    addresses.append(transaction_output.get("addr"))
            pass
    return addresses
