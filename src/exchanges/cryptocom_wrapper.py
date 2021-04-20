from cryptocom.exchange import ApiError

from src.exchanges.exchange_interface import CryptoExchangeInterface
from src.model.transaction import TradeData
from typing import List
import src.config as config
from pprint import pprint
import cryptocom.exchange as cro
from syncer import sync


@CryptoExchangeInterface.register
class CryptoComExchangeInterface:

    connected = False
    exchange = None
    account = None

    invalid_trading_pairs = []

    def __init__(self):
        pass

    async def connect(self):
        self.exchange = cro.Exchange()
        await self.exchange.sync_pairs()
        self.account = cro.Account(api_key=config.cryptocom_api_key, api_secret=config.cryptocom_api_secret)
        await self.account.sync_pairs()
        await self.account.get_balance()
        self.connected = True

    def get_invalid_trading_pairs(self):
        return self.invalid_trading_pairs

    @sync
    async def get_lendings(self):
        if not self.connected:
            await self.connect()
        return []

    @sync
    async def get_trades(self, from_timestamp, to_timestamp, list_of_trading_pairs) -> List[TradeData]:
        if not self.connected:
            await self.connect()

        exchange_traded_pairs = await self.exchange.get_pairs()

        coin_balances = await self.account.get_balance()

        for coin_balance in coin_balances:
            for traded_pair in exchange_traded_pairs:
                pass

        return []


def get_trading_pair_message_log(list_of_trading_pairs):
    log_message = "Trading pairs: ["
    trading_pair_counter = 0
    for trading_pair in list_of_trading_pairs:
        if trading_pair_counter > 0:
            log_message += ","
        log_message += " \"" + trading_pair.pair + "\" "
        trading_pair_counter += 1
    log_message += "]"
    return log_message


@sync
async def can_connect() -> bool:
    try:
        account = cro.Account(api_key=config.cryptocom_api_key, api_secret=config.cryptocom_api_secret)
        try:
            balances = await account.get_balance()
        except ApiError as e:
            return False
        return balances is not None
    except Exception as e:
        pprint(e)
        return False
