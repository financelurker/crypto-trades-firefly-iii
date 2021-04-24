import os

from cryptocom.exchange import ApiError

from exchanges.exchange_interface import AbstractCryptoExchangeClient, AbstractCryptoExchangeClientModule
from model.savings import InterestData
from model.transaction import TradeData, TradingPair
from typing import List, Dict, Mapping
import cryptocom.exchange as cro
from syncer import sync

exchange_name = "Crypto.com"


class CryptoComConfig(Dict):
    failed = False
    enabled = False
    initialized = False

    def init(self):
        try:
            self.setdefault("API_KEY", os.environ['CRYPTOCOM_API_KEY'])
            self.setdefault("API_SECRET", os.environ['CRYPTOCOM_API_SECRET'])
            self.initialized = True
            self.enabled = True
        except Exception as e:
            self.failed = True


@AbstractCryptoExchangeClientModule.register
class CryptoComClientModule(AbstractCryptoExchangeClientModule):

    @staticmethod
    def get_instance():
        return CryptoComClientModule()

    def get_exchange_client(self) -> AbstractCryptoExchangeClient:
        return CryptoComClient()

    def get_exchange_name(self) -> str:
        return exchange_name

    def get_config_entries(self) -> List[str]:
        return [
            "CRYPTOCOM_API_KEY",
            "CRYPTOCOM_API_SECRET"
        ]

@AbstractCryptoExchangeClient.register
class CryptoComClient(AbstractCryptoExchangeClient):

    connected = False
    exchange = None
    account = None
    list_of_pairs: dict = {}

    def __init__(self):
        pass

    @sync
    async def get_trading_pairs(self, list_of_symbols_and_codes):
        if not self.connected:
            await self.connect()

        result = []
        potential_trading_pairs = []
        exchange_traded_pairs = await self.exchange.get_pairs()

        for symbol_or_code in list_of_symbols_and_codes:
            for traded_symbol_or_code in list_of_symbols_and_codes:
                if symbol_or_code == traded_symbol_or_code:
                    continue
                new_trading_pair = TradingPair(symbol_or_code, traded_symbol_or_code)
                potential_trading_pairs.append(new_trading_pair)

        for traded_pair in exchange_traded_pairs:
            for potential_trading_pair in potential_trading_pairs:
                if traded_pair.base_coin.name == potential_trading_pair.security and \
                        traded_pair.quote_coin.name == potential_trading_pair.currency:
                    result.append(potential_trading_pair)
                    self.list_of_pairs.setdefault(traded_pair.name, traded_pair)

        return result

    @sync
    async def get_trades(self, from_timestamp, to_timestamp, list_of_trading_pairs) -> List[TradeData]:
        for trading_pair in list_of_trading_pairs:
            pair = self.list_of_pairs.get(trading_pair.security + "_" + trading_pair.currency)
            load_more = True
            page = 0
            while (load_more):
                trades = await self.account.get_trades(pair, page)
                if len(trades) < 200:
                    load_more = False
                pass

        return []

    @sync
    async def get_savings_interests(self, from_timestamp: int, to_timestamp: int, list_of_assets: List[str]) -> List[InterestData]:
        if not self.connected:
            await self.connect()
        return []

    async def connect(self):
        self.exchange = cro.Exchange()
        await self.exchange.sync_pairs()
        config = CryptoComConfig()
        config.init()
        self.account = cro.Account(api_key=config.get("API_KEY"), api_secret=config.get("API_SECRET"))
        await self.account.sync_pairs()
        await self.account.get_balance()
        self.connected = True
