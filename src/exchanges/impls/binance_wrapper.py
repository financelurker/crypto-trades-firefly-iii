from __future__ import print_function
from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime

from backend.firefly_wrapper import TransactionCollection
from exchanges.exchange_interface import CryptoExchangeInterface, CryptoExchangeModuleMetaClass
from model.transaction import TradeData, TransactionType
from pprint import pprint
from typing import List

import config as config

exchange_name = "Binance"


@CryptoExchangeModuleMetaClass.register
class BinanceModuleMetaClass(CryptoExchangeModuleMetaClass):

    @staticmethod
    def get_instance():
        return BinanceModuleMetaClass()

    def get_exchange_client(self) -> CryptoExchangeInterface:
        return BinanceExchangeInterface()

    def get_exchange_name(self) -> str:
        return exchange_name

    def get_config_entries(self) -> List[str]:
        return [
            "BINANCE_API_KEY",
            "BINANCE_API_SECRET"
        ]

    def can_connect(self) -> bool:
        try:
            new_client = Client(config.binance_api_key, config.binance_api_secret)
            new_client.get_account()
            return True
        except:
            return False


@CryptoExchangeInterface.register
class BinanceExchangeInterface(CryptoExchangeInterface):
    client = None
    invalid_trading_pairs = []

    def __init__(self):
        self.connect()

    def connect(self):
        try:
            if config.debug:
                print('Binance: Trying to connect to your account...')
            new_client = Client(config.binance_api_key, config.binance_api_secret)
            new_client.get_account()
            if config.debug:
                print('Binance: Connection to your account established.')
            self.client = new_client

            lending_account = self.client.get_lending_account()
            lending_position = self.client.get_lending_position()
            lending_product_list = self.client.get_lending_product_list()
            lending_interest_history_flexible = self.client.get_lending_interest_history(lendingType="DAILY")
            lending_interest_history_activity = self.client.get_lending_interest_history(lendingType="ACTIVITY")
            lending_interest_history_fixed = self.client.get_lending_interest_history(lendingType="CUSTOMIZED_FIXED")

            #        lending_purchase_history = client.get_lending_purchase_history()
            #        lending_daily_quota_left = client.get_lending_daily_quota_left()
            #        lending_redemption_list = client.get_lending_redemption_history()
        except Exception as e:
            print('Binance: Cannot connect to your account.' % e)
            raise Exception('Binance: Cannot connect to your account.', e)

    def get_invalid_trading_pairs(self) -> List[str]:
        return self.invalid_trading_pairs

    def get_lending_and_staking_interest(self):
        pass

    def get_trades(self, from_timestamp, to_timestamp, list_of_trading_pairs) -> List[TradeData]:
        list_of_trades: List[TradeData] = []

        if config.debug:
            print("Binance:   Get trades from " + str(datetime.fromtimestamp(from_timestamp / 1000)) + " to " + str(
            datetime.fromtimestamp(to_timestamp / 1000 - 1)))
            trading_pairs_log_message = self.get_trading_pair_message_log(list_of_trading_pairs)
            print(trading_pairs_log_message)

        for trading_pair in list_of_trading_pairs:
            try:
                if (to_timestamp - from_timestamp) / 1000 - 1 > 60 * 60 * 24:
                    trades_total = self.client.get_my_trades(symbol=trading_pair.pair)
                    relevant_trades = []
                    for trade in trades_total:
                        if int(trade.get('time')) - from_timestamp >= 0:
                            relevant_trades.append(trade)
                    my_trades = relevant_trades
                else:
                    my_trades = self.client.get_my_trades(symbol=trading_pair.pair, startTime=from_timestamp, endTime=to_timestamp)
                if len(my_trades) > 0:
                    list_of_trades.extend(transform_to_trade_data(my_trades, trading_pair))
                    if config.debug:
                        print("Binance:   Found " + str(len(my_trades)) + " trades for " + trading_pair.pair)
            except BinanceAPIException as e:
                if e.status_code == 400 and e.code == -1100:
                    # print("Invalid character found in trading pair: " + trading_pair)
                    self.invalid_trading_pairs.append(trading_pair.pair)
                elif e.status_code == 400 and e.code == -1121:
                    # print("Invalid trading pair found: " + trading_pair)
                    self.invalid_trading_pairs.append(trading_pair.pair)
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
            log_message += " \"" + trading_pair.pair + "\" "
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
