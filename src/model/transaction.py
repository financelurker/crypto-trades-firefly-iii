from enum import Enum


class TradeData(object):
    def __init__(self, trading_platform, commission_amount, commission_asset, currency_amount, security_amount, trading_pair, type, trade_id, trade_time):
        self.trading_platform = trading_platform
        self.commission_amount = commission_amount
        self.commission_asset = commission_asset
        self.currency_amount = currency_amount
        self.security_amount = security_amount
        self.trading_pair = trading_pair
        self.type: TransactionType = type
        self.id = trade_id
        self.time = trade_time


class TransactionType(Enum):
    BUY = 1
    SELL = 2


known_trading_pairs = []

class TradingPair(object):
    def __init__(self, from_coin, to_coin, pair):
        self.security = from_coin
        self.currency = to_coin
        self.pair = pair
