import src.config as config
import src.firefly.firefly_wrapper as firefly_wrapper
from src.model.transaction import TransactionCollection, TradeData, CollectionType, TradingPair
from src.exchanges import exchange_interface_factory


def get_relevant_trading_pair_from_binance_trade(binance_trade, list_of_trading_pairs):
    for trading_pair in list_of_trading_pairs:
        if trading_pair.pair in binance_trade.get('symbol'):
            return trading_pair
    exit(-9999)


def process_buy_trades(list_of_buy, trading_pair, trading_platform):
    list_of_new_transaction_collections = []
    for buy in list_of_buy:
        commission_amount = buy.get('commission')
        commission_asset = buy.get('commissionAsset')
        currency_amount = buy.get('qty')
        security_amount = buy.get('quoteQty')
        trade_id = buy.get('id')
        trade_time = buy.get('time')
        trade_data = TradeData(trading_platform, commission_amount, commission_asset, currency_amount, security_amount, trading_pair, trade_id, trade_time)
        new_transaction_collection = TransactionCollection(trade_data, None, None, None, CollectionType.BUY, None)
        list_of_new_transaction_collections.append(new_transaction_collection)
    return list_of_new_transaction_collections


def process_sell_trades(list_of_sell, trading_pair, trading_platform):
    list_of_new_transaction_collections = []
    for sell in list_of_sell:
        commission_amount = sell.get('commission')
        commission_asset = sell.get('commissionAsset')
        currency_amount = sell.get('quoteQty')
        security_amount = sell.get('qty')
        trade_id = sell.get('id')
        trade_time = sell.get('time')
        trade_data = TradeData(trading_platform, commission_amount, commission_asset, currency_amount, security_amount, trading_pair, trade_id, trade_time)
        new_transaction_collection = TransactionCollection(trade_data, None, None, None, CollectionType.SELL, None)
        list_of_new_transaction_collections.append(new_transaction_collection)
    return list_of_new_transaction_collections


def binance_trades_of_trading_pair_processor(list_of_binance_trades, list_of_trading_pairs, trading_platform):
    list_of_buy = []
    list_of_sell = []
    trading_pair = None

    for binance_trade in list_of_binance_trades:
        if binance_trade.get('isBuyer'):
            is_buy_order = True
            is_sell_order = False
        else:
            is_buy_order = False
            is_sell_order = True
        if trading_pair is None:
            trading_pair = get_relevant_trading_pair_from_binance_trade(binance_trade, list_of_trading_pairs)
        if is_buy_order:
            list_of_buy.append(binance_trade)
        elif is_sell_order:
            list_of_sell.append(binance_trade)

    result = []

    result.extend(process_buy_trades(list_of_buy, trading_pair, trading_platform))
    result.extend(process_sell_trades(list_of_sell, trading_pair, trading_platform))

    return result


def binance_trades_of_trading_pairs_processor(binance_trades_of_trading_pairs, list_of_trading_pairs, trading_platform):
    result = []
    for list_of_binance_trades in binance_trades_of_trading_pairs:
        result.extend(binance_trades_of_trading_pair_processor(list_of_binance_trades, list_of_trading_pairs, trading_platform))
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
    if transaction_collection.collection_type is CollectionType.BUY:
        if firefly_account_collection.security == transaction_collection.trade_data.trading_pair.security:
            transaction_collection.to_ff_account = firefly_account_collection.asset_account.attributes
        if firefly_account_collection.security == transaction_collection.trade_data.trading_pair.currency:
            transaction_collection.from_ff_account = firefly_account_collection.asset_account.attributes

    elif transaction_collection.collection_type is CollectionType.SELL:
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
    binance_trades_of_trading_pairs = exchange_interface.get_trades(from_timestamp, to_timestamp, list_of_trading_pairs)
    list_of_trading_pairs = remove_invalid_trading_pairs(list_of_trading_pairs, exchange_interface.get_invalid_trading_pairs())
    if len(binance_trades_of_trading_pairs) == 0:
        print(trading_platform + ": No new trades found...")
        return "ok"

    print(trading_platform + ': 3. Getting accounts and currencies from Firefly III')
    firefly_account_collections = firefly_wrapper.get_firefly_account_collections_for_pairs(list_of_trading_pairs, trading_platform)

    print(trading_platform + ': 4. Create new transaction collections, prepare import')
    new_transaction_collections = binance_trades_of_trading_pairs_processor(binance_trades_of_trading_pairs,
                                                                            list_of_trading_pairs, trading_platform)
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
