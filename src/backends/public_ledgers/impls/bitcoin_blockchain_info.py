from syncer import sync
import aiohttp

from backends.public_ledgers.api import SupportedBlockchainExplorer, SupportedBlockchainModule
from model.ledger_transaction import LedgerTransaction

# Module config
name = "Bitcoin"
currency_code = "BTC"
address_identifier = "xpub"
address_regular_expression = r"xpub=\"([a-zA-Z0-9]*)\""

# Backend config
base_url = "https://blockchain.info"
address_uri = "/multiaddr?active="
transaction_uri = "/rawtx/"


@SupportedBlockchainModule.register
class BitcoinModule(SupportedBlockchainModule):

    def get_blockchain_explorer(self) -> SupportedBlockchainExplorer:
        return BitcoinExplorer()

    def get_blockchain_name(self) -> str:
        return name

    def is_enabled(self) -> bool:
        return True

    @staticmethod
    def get_instance():
        return BitcoinModule()


@SupportedBlockchainExplorer.register
class BitcoinExplorer(SupportedBlockchainExplorer):

    def get_address_identifier(self) -> str:
        return address_identifier

    def get_address_re(self) -> str:
        return address_regular_expression

    @sync
    async def get_tx_addresses_from_address(self, address: str, timeout=25):
        timeout = aiohttp.ClientTimeout(timeout)
        addresses = []

        async with aiohttp.ClientSession(timeout=timeout) as session:
            page = 0
            page_size = 50
            load_next = True
            while load_next:
                resp = await session.request(method="get",
                                             url=base_url + address_uri + address + "&n=" + str(
                                                 page_size) + "&offset=" + str(
                                                 page_size * page))
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

    def get_blockchain_name(self) -> str:
        return name

    def get_currency_code(self) -> str:
        return currency_code

    @sync
    async def get_transaction_from_ledger(self, tx_id, timeout=25) -> LedgerTransaction:
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
