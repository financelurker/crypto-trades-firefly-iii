import backends.exchanges as exchanges
from backends.exchanges.exchange_interface import AbstractCryptoExchangeClient


def get_specific_exchange_interface(trading_platform: str) -> AbstractCryptoExchangeClient:
    for instance in exchanges.list_of_impl_meta_class_instances:
        if trading_platform == instance.get_exchange_name():
            return instance.get_exchange_client()

    raise Exception("The exchange \"" + trading_platform + "\" is not supported by now!")
