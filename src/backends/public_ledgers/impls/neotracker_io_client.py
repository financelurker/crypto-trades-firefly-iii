from typing import List

from syncer import sync
import aiohttp

from backends.public_ledgers import SupportedBlockchainModule, SupportedBlockchainExplorer
from model.ledger_transaction import LedgerTransaction


# Module config
name = "Neo"
currency_code = "NEO"
address_identifier = "address"
address_regular_expression = r"address=\"([a-zA-Z0-9]*)\""

# Backend config
base_url = "https://neoscan.io"
last_transactions_uri = "/api/main_net/v1/get_last_transactions_by_address/{address}/{page}"
get_transaction_uri = "/api/main_net/v1/get_transaction/"


@SupportedBlockchainModule.register
class NeoExplorerModule(SupportedBlockchainModule):

    def get_blockchain_explorer(self) -> SupportedBlockchainExplorer:
        return NeoExplorer()

    def get_blockchain_name(self) -> str:
        return "NEO"

    def is_enabled(self) -> bool:
        return True

    @staticmethod
    def get_instance(cls):
        return NeoExplorerModule()


@SupportedBlockchainExplorer.register
class NeoExplorer(SupportedBlockchainExplorer):

    def get_tx_addresses_from_address(self, address: str, timeout=25) -> List[str]:
        return [address]

    def get_blockchain_name(self) -> str:
        return name

    def get_currency_code(self) -> str:
        return currency_code

    def get_address_identifier(self) -> str:
        return address_identifier

    def get_address_re(self) -> str:
        return address_regular_expression

    @sync
    async def get_transaction_from_ledger(self, tx_id, timeout=25) -> LedgerTransaction:
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
