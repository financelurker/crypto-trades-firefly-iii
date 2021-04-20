import abc
from typing import List
from src.model.transaction import TradingPair


class CryptoExchangeInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.connect) and
                hasattr(subclass, 'can_connect') and
                callable(subclass.get_invalid_trading_pairs) and
                hasattr(subclass, 'get_invalid_trading_pairs') and
                callable(subclass.get_trades) and
                hasattr(subclass, 'get_trades') and
                callable(subclass.get_lendings) and
                hasattr(subclass, 'get_lendings') or
                NotImplemented)

    @abc.abstractmethod
    def can_connect(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def get_invalid_trading_pairs(self) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_trades(self, from_timestamp: int, to_timestamp: int, list_of_trading_pairs: List[TradingPair]):
        raise NotImplementedError

    @abc.abstractmethod
    def get_lendings(self):
        raise NotImplementedError
