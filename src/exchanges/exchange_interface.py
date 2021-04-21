import abc
from typing import List

from model.transaction import TradingPair, TradeData


class CryptoExchangeInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.connect) and
                hasattr(subclass, 'get_invalid_trading_pairs') and
                callable(subclass.get_trades) and
                hasattr(subclass, 'get_trades') and
                callable(subclass.get_lending_and_staking_interest) and
                hasattr(subclass, 'get_lending_and_staking_interest') or
                NotImplemented)

    @abc.abstractmethod
    def get_invalid_trading_pairs(self) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_trades(self, from_timestamp: int, to_timestamp: int, list_of_trading_pairs: List[TradingPair]) -> List[List[TradeData]]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_lending_and_staking_interest(self):
        raise NotImplementedError


class CryptoExchangeModuleMetaClass(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.get_exchange_client) and
                hasattr(subclass, 'get_exchange_client') and
                callable(subclass.get_exchange_name) and
                hasattr(subclass, 'get_exchange_name') and
                callable(subclass.get_config_entries) and
                hasattr(subclass, 'get_config_entries') and
                callable(subclass.can_connect) and
                hasattr(subclass, 'can_connect') or
                NotImplemented)

    @abc.abstractmethod
    def get_exchange_client(self) -> CryptoExchangeInterface:
        raise NotImplementedError
        # return here the instance of your client implementation

    @abc.abstractmethod
    def get_exchange_name(self) -> str:
        raise NotImplementedError
        # return here the exchange name which will be used for logging and user-interaction purposes

    @abc.abstractmethod
    def get_config_entries(self) -> List[str]:
        raise NotImplementedError
        # return here the relevant configuration items needed for the specific client implementation

    @abc.abstractmethod
    def can_connect(self) -> bool:
        raise NotImplementedError
        # determines whether or not the plugin can connect to the exchange

