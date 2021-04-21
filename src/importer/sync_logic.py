import config as config
import backend.firefly_wrapper as firefly_wrapper
from model.transaction import TradeData, TradingPair, TransactionType
from exchanges import exchange_interface_factory
from backend.firefly_wrapper import TransactionCollection
from typing import List


def get_transaction_collections_from_trade_data(list_of_trades: List[TradeData]):
    result = []
    for trade in list_of_trades:
        result.append(TransactionCollection(trade, None, None, None, None))
    return result


def get_list_of_trading_pairs(list_of_symbols_and_codes):
    list_of_trading_pairs = []
    for symbol_or_code in list_of_symbols_and_codes:
        for traded_symbol_or_code in list_of_symbols_and_codes:
            if symbol_or_code == traded_symbol_or_code:
                continue
            new_trading_pair = TradingPair(symbol_or_code, traded_symbol_or_code,
                                           symbol_or_code + traded_symbol_or_code)
            list_of_trading_pairs.append(new_trading_pair)
    return list_of_trading_pairs


def remove_invalid_trading_pairs(list_of_all_trading_pairs, invalid_trading_pairs):
    invalid = []
    result = []
    for invalid_trading_pair in invalid_trading_pairs:
        for trading_pair in list_of_all_trading_pairs:
            if invalid_trading_pair in trading_pair.pair:
                invalid.append(trading_pair)
    for invalid_trading_pair in invalid:
        list_of_all_trading_pairs.remove(invalid_trading_pair)
    for trading_pair in list_of_all_trading_pairs:
        result.append(trading_pair)
    return result


def augment_transaction_collection_with_firefly_accounts(transaction_collection, firefly_account_collection):
    if transaction_collection.trade_data.type is TransactionType.BUY:
        if firefly_account_collection.security == transaction_collection.trade_data.trading_pair.security:
            transaction_collection.to_ff_account = firefly_account_collection.asset_account.attributes
        if firefly_account_collection.security == transaction_collection.trade_data.trading_pair.currency:
            transaction_collection.from_ff_account = firefly_account_collection.asset_account.attributes

    elif transaction_collection.trade_data.type is TransactionType.SELL:
        if firefly_account_collection.security == transaction_collection.trade_data.trading_pair.currency:
            transaction_collection.to_ff_account = firefly_account_collection.asset_account.attributes
        if firefly_account_collection.security == transaction_collection.trade_data.trading_pair.security:
            transaction_collection.from_ff_account = firefly_account_collection.asset_account.attributes

    else:
        pass

    if firefly_account_collection.security == transaction_collection.trade_data.commission_asset:
        transaction_collection.commission_account = firefly_account_collection.expense_account.attributes
    commission_asset = transaction_collection.trade_data.commission_asset

    if commission_asset in firefly_account_collection.asset_account.attributes.currency_symbol \
            or commission_asset in firefly_account_collection.asset_account.attributes.currency_code:
        transaction_collection.from_commission_account = firefly_account_collection.asset_account.attributes


def augment_transaction_collections_with_firefly_accounts(transaction_collections, firefly_account_collections):
    for transaction_collection in transaction_collections:
        for firefly_account_collection in firefly_account_collections:
            augment_transaction_collection_with_firefly_accounts(transaction_collection, firefly_account_collection)


def interval_processor(from_timestamp, to_timestamp, init, trading_platform):
    exchange_interface = exchange_interface_factory.get_specific_exchange_interface(trading_platform)

    epochs_to_calculate = get_epochs_differences(from_timestamp, to_timestamp, config.sync_inverval)
    if init:
        header_log = trading_platform + ': Importing all historical trades from ' + str(from_timestamp) + " to " + str(to_timestamp)
    else:
        header_log = trading_platform + ': Importing trades from ' + str(from_timestamp) + " to " + str(to_timestamp) + ", " + str(epochs_to_calculate) + " intervals."
    if config.debug:
        print(header_log)

    print(trading_platform + ': 1. Get eligible symbols from existing asset accounts within Firefly III')
    list_of_symbols_and_codes = firefly_wrapper.get_symbols_and_codes(trading_platform)
    list_of_all_trading_pairs = get_list_of_trading_pairs(list_of_symbols_and_codes)

    print(trading_platform + ': 2. Getting trades from crypto currency exchange')
    list_of_trading_pairs = remove_invalid_trading_pairs(list_of_all_trading_pairs, exchange_interface.get_invalid_trading_pairs())
    list_of_trade_data = exchange_interface.get_trades(from_timestamp, to_timestamp, list_of_trading_pairs)
    list_of_trading_pairs = remove_invalid_trading_pairs(list_of_trading_pairs, exchange_interface.get_invalid_trading_pairs())
    if len(list_of_trade_data) == 0:
        print(trading_platform + ": No new trades found...")
        return "ok"

    print(trading_platform + ': 3. Getting accounts and currencies from Firefly III')
    firefly_account_collections = firefly_wrapper.get_firefly_account_collections_for_pairs(list_of_trading_pairs, trading_platform)

    print(trading_platform + ': 4. Create new transaction collections, prepare import')
    new_transaction_collections = get_transaction_collections_from_trade_data(list_of_trade_data)
    augment_transaction_collections_with_firefly_accounts(new_transaction_collections, firefly_account_collections)

    print(trading_platform + ': 5. Importing new trades as transactions to Firefly III')
    firefly_wrapper.import_transaction_collections(new_transaction_collections, trading_platform)

    print(trading_platform + ": 6. Finishing import and going to sleep")
    return "ok"


def get_epochs_differences(previous_last_begin_timestamp, last_begin_timestamp, sync_inverval):
    if sync_inverval == 'hourly':
        return int(last_begin_timestamp / 1000 / 60 / 60) - int(previous_last_begin_timestamp / 1000 / 60 / 60)
    elif sync_inverval == 'daily':
        return int(last_begin_timestamp / 1000 / 60 / 60 / 24) - int(
            previous_last_begin_timestamp / 1000 / 60 / 60 / 24)
    elif sync_inverval == 'debug':
        return int(last_begin_timestamp / 1000 / 10) - int(previous_last_begin_timestamp / 1000 / 10)
    else:
        print("The configured interval is not supported. Use 'hourly' or 'daily' within your config.")
        exit(-749)
