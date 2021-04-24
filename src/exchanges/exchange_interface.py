import abc
from typing import List

from model.savings import InterestData
from model.transaction import TradingPair, TradeData


class AbstractCryptoExchangeClient(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.get_trading_pairs) and
                hasattr(subclass, 'get_trading_pairs') and
                callable(subclass.get_trades) and
                hasattr(subclass, 'get_trades') and
                callable(subclass.get_savings_interests) and
                hasattr(subclass, 'get_savings_interests') or
                NotImplemented)

    @abc.abstractmethod
    def get_trading_pairs(self, list_of_symbols_and_codes: List[str]) -> List[TradingPair]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_trades(self, from_timestamp: int, to_timestamp: int, list_of_trading_pairs: List[TradingPair]) -> List[TradeData]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_savings_interests(self, from_timestamp: int, to_timestamp: int, list_of_assets: List[str]) -> List[InterestData]:
        raise NotImplementedError


class AbstractCryptoExchangeClientModule(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.get_exchange_client) and
                hasattr(subclass, 'get_exchange_client') and
                callable(subclass.get_exchange_name) and
                hasattr(subclass, 'get_exchange_name') and
                callable(subclass.is_enabled) and
                hasattr(subclass, 'is_enabled') or
                NotImplemented)

    @abc.abstractmethod
    def get_exchange_client(self) -> AbstractCryptoExchangeClient:
        raise NotImplementedError
        # return here the instance of your client implementation

    @abc.abstractmethod
    def get_exchange_name(self) -> str:
        raise NotImplementedError
        # return here the exchange name which will be used for logging and user-interaction purposes

    @abc.abstractmethod
    def is_enabled(self) -> bool:
        raise NotImplementedError
        # return here if the plugin is enabled and all needed configuration is set
