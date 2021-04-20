from src.exchanges.exchange_interface import CryptoExchangeInterface
from src.exchanges import cryptocom_wrapper, binance_wrapper
from src.exchanges.binance_wrapper import BinanceExchangeInterface
from src.exchanges.cryptocom_wrapper import CryptoComExchangeInterface


def is_exchange_available(trading_platform: str) -> bool:
    if trading_platform.lower() == "binance":
        return binance_wrapper.can_connect()
    elif trading_platform.lower() == "crypto.com":
        return True
    else:
        return False


def get_specific_exchange_interface(trading_platform: str) -> CryptoExchangeInterface:
    if trading_platform.lower() == "binance":
        if binance_wrapper.can_connect():
            return BinanceExchangeInterface()
        else:
            raise Exception("Cannot connect to Binance API services.")
    elif trading_platform.lower() == "crypto.com":
        if cryptocom_wrapper.can_connect():
            return CryptoComExchangeInterface()
        else:
            raise Exception("Cannot connect to Crypto.com API services. Check the the internet connection and the API keys and API secrets!")
    else:
        raise Exception("The exchange \"" + trading_platform + "\" is not supported by now!")
