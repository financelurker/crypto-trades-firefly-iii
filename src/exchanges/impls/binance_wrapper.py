from __future__ import print_function

import os

from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime

from backend.firefly_wrapper import TransactionCollection
from exchanges.exchange_interface import AbstractCryptoExchangeClient, AbstractCryptoExchangeClientModule
from model.savings import InterestData, InterestDue, SavingsType
from model.transaction import TradeData, TransactionType, TradingPair
from pprint import pprint
from typing import List, Dict
import config as base_config

exchange_name = "Binance"


class BinanceConfig(Dict):
    failed = False
    enabled = False
    initialized = False
    api_key = None
    api_secret = None

    def init(self):
        try:
            self.api_key =  os.environ['BINANCE_API_KEY']
            self.api_secret = os.environ['BINANCE_API_SECRET']
            self.initialized = True
            self.enabled = True
        except Exception as e:
            self.failed = True


@AbstractCryptoExchangeClientModule.register
class BinanceClientModule(AbstractCryptoExchangeClientModule):

    @staticmethod
    def get_instance():
        return BinanceClientModule()

    def get_exchange_client(self) -> AbstractCryptoExchangeClient:
        return BinanceClient()

    def get_exchange_name(self) -> str:
        return exchange_name

    def is_enabled(self) -> bool:
        config = BinanceConfig()
        config.init()
        return config.enabled


def get_interest_data_from_binance_data(binance_data, type, due) -> InterestData:
    amount = binance_data.get('interest')
    currency = binance_data.get('asset')
    date = datetime.fromtimestamp(int(binance_data.get('time')) / 1000)

    return InterestData(type, amount, currency, date, due)


def get_interests_from_binance_data(interests_binance_data, savings_type, interest_due) -> List[InterestData]:
    result = []
    for interest_binance_data in interests_binance_data:
        inner = get_interest_data_from_binance_data(interest_binance_data, savings_type, interest_due)
        result.append(inner)
    return result


@AbstractCryptoExchangeClient.register
class BinanceClient(AbstractCryptoExchangeClient):
    client = None
    config = BinanceConfig()
    config.init()

    def __init__(self):
        self.connect()

    def connect(self):
        try:
            if base_config.debug:
                print('Binance: Trying to connect to your account...')
            new_client = Client(self.config.api_key, self.config.api_secret)
            if not new_client.get_account_status().get('success') == True:
                raise Exception("Binance: Cannot access your account status.")
            withdraw_history = new_client.get_withdraw_history()
            deposit_history = new_client.get_deposit_history()
            new_client.get_account_status()
            if base_config.debug:
                print('Binance: Connection to your account established.')
            self.client = new_client
        except Exception as e:
            print('Binance: Cannot connect to your account.' % e)
            raise Exception('Binance: Cannot connect to your account.', e)

    def get_trading_pairs(self, list_of_symbols_and_codes: List[str]) -> List[TradingPair]:
        binance_products = self.client.get_products().get('data')
        potential_trading_pairs = []
        result = []

        for symbol_or_code in list_of_symbols_and_codes:
            for traded_symbol_or_code in list_of_symbols_and_codes:
                if symbol_or_code == traded_symbol_or_code:
                    continue
                new_trading_pair = TradingPair(symbol_or_code, traded_symbol_or_code)
                potential_trading_pairs.append(new_trading_pair)

        for product in binance_products:
            for potential_trading_pair in potential_trading_pairs:
                if product.get('st') == 'TRADING' and \
                        product.get('b') == potential_trading_pair.security and \
                        product.get('q') == potential_trading_pair.currency:
                    result.append(potential_trading_pair)

        return result

    def get_savings_interests(self, from_timestamp, to_timestamp, list_of_assets) -> List[InterestData]:
        if base_config.debug:
            print("Binance:   Get interest from " + str(datetime.fromtimestamp(from_timestamp / 1000)) + " to " + str(
                datetime.fromtimestamp(to_timestamp / 1000 - 1)))
        result = []
        lending_interest_history_daily = self.client.get_lending_interest_history(lendingType="DAILY", startTime=from_timestamp, endTime=to_timestamp, size=100)
        result.extend(get_interests_from_binance_data(lending_interest_history_daily, SavingsType.LENDING, InterestDue.DAILY))
        lending_interest_history_activity = self.client.get_lending_interest_history(lendingType="ACTIVITY", startTime=from_timestamp, endTime=to_timestamp, size=100)
        result.extend(get_interests_from_binance_data(lending_interest_history_activity, SavingsType.LENDING, InterestDue.ACTIVE))
        lending_interest_history_fixed = self.client.get_lending_interest_history(lendingType="CUSTOMIZED_FIXED", startTime=from_timestamp, endTime=to_timestamp, size=100)
        result.extend(get_interests_from_binance_data(lending_interest_history_fixed, SavingsType.LENDING, InterestDue.FIXED))
        return result

    def get_trades(self, from_timestamp, to_timestamp, list_of_trading_pairs) -> List[TradeData]:
        list_of_trades: List[TradeData] = []

        if base_config.debug:
            print("Binance:   Get trades from " + str(datetime.fromtimestamp(from_timestamp / 1000)) + " to " + str(
            datetime.fromtimestamp(to_timestamp / 1000 - 1)))
            trading_pairs_log_message = self.get_trading_pair_message_log(list_of_trading_pairs)
            print(trading_pairs_log_message)

        for trading_pair in list_of_trading_pairs:
            try:
                if (to_timestamp - from_timestamp) / 1000 - 1 > 60 * 60 * 24:
                    trades_total = self.client.get_my_trades(symbol=trading_pair.security + trading_pair.currency)
                    relevant_trades = []
                    for trade in trades_total:
                        if int(trade.get('time')) - from_timestamp >= 0:
                            relevant_trades.append(trade)
                    my_trades = relevant_trades
                else:
                    my_trades = self.client.get_my_trades(symbol=trading_pair.security + trading_pair.currency, startTime=from_timestamp, endTime=to_timestamp)
                if len(my_trades) > 0:
                    list_of_trades.extend(transform_to_trade_data(my_trades, trading_pair))
                    if base_config.debug:
                        print("Binance:   Found " + str(len(my_trades)) + " trades for " + trading_pair.security + trading_pair.currency)
            except BinanceAPIException as e:
                if e.status_code == 400 and e.code == -1100:
                    # print("Invalid character found in trading pair: " + trading_pair)
                    # self.invalid_trading_pairs.append(trading_pair.security + trading_pair.currency)
                    pass
                elif e.status_code == 400 and e.code == -1121:
                    # print("Invalid trading pair found: " + trading_pair)
                    # self.invalid_trading_pairs.append(trading_pair.security + trading_pair.currency)
                    pass
                else:
                    pprint(e)

        return list_of_trades

    @staticmethod
    def get_trading_pair_message_log(list_of_trading_pairs):
        log_message = "Binance:   Trading pairs: ["
        trading_pair_counter = 0
        for trading_pair in list_of_trading_pairs:
            if trading_pair_counter > 0:
                log_message += ","
            log_message += " \"" + trading_pair.security + trading_pair.currency + "\" "
            trading_pair_counter += 1
        log_message += "]"
        return log_message


def transform_buy_trade(buy, trading_pair) -> TradeData:
    commission_amount = buy.get('commission')
    commission_asset = buy.get('commissionAsset')
    currency_amount = buy.get('qty')
    security_amount = buy.get('quoteQty')
    trade_id = buy.get('id')
    trade_time = buy.get('time')
    trading_platform = exchange_name
    result = TradeData(trading_platform, commission_amount, commission_asset, currency_amount, security_amount,
                           trading_pair, TransactionType.BUY, trade_id, trade_time)
    return result


def transform_sell_trade(sell, trading_pair) -> TradeData:
    commission_amount = sell.get('commission')
    commission_asset = sell.get('commissionAsset')
    currency_amount = sell.get('quoteQty')
    security_amount = sell.get('qty')
    trade_id = sell.get('id')
    trade_time = sell.get('time')
    trading_platform = exchange_name
    return TradeData(trading_platform, commission_amount, commission_asset, currency_amount, security_amount,
                           trading_pair, TransactionType.SELL, trade_id, trade_time)


def transform_to_trade_data(my_trades, trading_pair) -> List[TradeData]:
    result = []

    for trade in my_trades:
        if trade.get('isBuyer'):
            result.append(transform_buy_trade(trade, trading_pair))
        else:
            result.append(transform_sell_trade(trade, trading_pair))

    return result
