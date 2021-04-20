from enum import Enum


class TradeData(object):
    def __init__(self, trading_platform, commission_amount, commission_asset, currency_amount, security_amount, trading_pair, trade_id, trade_time):
        self.trading_platform = trading_platform
        self.commission_amount = commission_amount
        self.commission_asset = commission_asset
        self.currency_amount = currency_amount
        self.security_amount = security_amount
        self.trading_pair = trading_pair
        self.id = trade_id
        self.time = trade_time


class TradingPair(object):
    def __init__(self, from_coin, to_coin, pair):
        self.security = from_coin
        self.currency = to_coin
        self.pair = pair


class TransactionCollection(object):
    def __init__(self, trade_data, _from_ff_account, _to_ff_account, _commission_ff_account,
                 _collection_type, _from_commission_account):
        self.trade_data = trade_data
        self.from_ff_account = _from_ff_account
        self.to_ff_account = _to_ff_account
        self.commission_account = _commission_ff_account
        self.collection_type = _collection_type
        self.from_commission_account = _from_commission_account


class CollectionType(Enum):
    BUY = 1
    SELL = 2
