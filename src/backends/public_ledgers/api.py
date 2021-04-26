import abc
from typing import List

from model.ledger_transaction import LedgerTransaction


class SupportedBlockchainExplorer(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.get_tx_addresses_from_address) and
                hasattr(subclass, 'get_tx_addresses_from_address') and
                callable(subclass.get_blockchain_name) and
                hasattr(subclass, 'get_blockchain_name') and
                callable(subclass.get_transaction_from_ledger) and
                hasattr(subclass, 'get_transaction_from_ledger') and
                callable(subclass.get_currency_code) and
                hasattr(subclass, 'get_currency_code') and
                callable(subclass.get_address_identifier) and
                hasattr(subclass, 'get_address_identifier') and
                callable(subclass.get_address_re) and
                hasattr(subclass, 'get_address_re') or
                NotImplemented)

    @abc.abstractmethod
    def get_blockchain_name(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_currency_code(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_address_identifier(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_address_re(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_tx_addresses_from_address(self, address: str, timeout=25) -> List[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def get_transaction_from_ledger(self, tx_id, timeout=25) -> LedgerTransaction:
        raise NotImplementedError


class SupportedBlockchainModule(metaclass=abc.ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (callable(subclass.get_blockchain_explorer) and
                hasattr(subclass, 'get_blockchain_explorer') and
                callable(subclass.get_blockchain_name) and
                hasattr(subclass, 'get_blockchain_name') and
                callable(subclass.is_enabled) and
                hasattr(subclass, 'is_enabled') or
                NotImplemented)

    @abc.abstractmethod
    def is_enabled(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def get_blockchain_name(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_blockchain_explorer(self) -> SupportedBlockchainExplorer:
        raise NotImplementedError
