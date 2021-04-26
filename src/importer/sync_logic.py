import config as config
import backends.firefly.firefly_wrapper as firefly_wrapper
from model.transaction import TradeData, TransactionType
from backends.exchanges import exchange_interface_factory
from backends.firefly.firefly_wrapper import TransactionCollection
from typing import List
import re
from backends.public_ledgers import available_explorer

def get_transaction_collections_from_trade_data(list_of_trades: List[TradeData]):
    result = []
    for trade in list_of_trades:
        result.append(TransactionCollection(trade, None, None, None, None))
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


def handle_deposits(from_timestamp, to_timestamp, init, trading_platform, exchange_interface,
                    firefly_account_collections, epochs_to_calculate):
    if init:
        header_log = trading_platform + ': Importing all historical deposits from ' + str(from_timestamp) + " to " + str(to_timestamp)
    else:
        header_log = trading_platform + ': Importing deposits from ' + str(from_timestamp) + " to " + str(to_timestamp) + ", " + str(epochs_to_calculate) + " intervals."
    if config.debug:
        print(header_log)

    print(trading_platform + ': 1. Get deposits from exchange')
    list_of_assets = []
    for account_collection in firefly_account_collections:
        list_of_assets.append(account_collection.security)
    deposits = exchange_interface.get_deposits(from_timestamp, to_timestamp, list_of_assets)

    if len(deposits) == 0:
        print(trading_platform + ':   No new deposits found.')
        return

    print(trading_platform + ": 2. Import deposits to Firefly III")
    firefly_wrapper.import_deposits(deposits, firefly_account_collections, trading_platform)


def handle_withdrawals(from_timestamp, to_timestamp, init, trading_platform, exchange_interface,
                     firefly_account_collections, epochs_to_calculate):
    if init:
        header_log = trading_platform + ': Importing all historical withdrawals from ' + str(from_timestamp) + " to " + str(to_timestamp)
    else:
        header_log = trading_platform + ': Importing withdrawals from ' + str(from_timestamp) + " to " + str(to_timestamp) + ", " + str(epochs_to_calculate) + " intervals."
    if config.debug:
        print(header_log)

    print(trading_platform + ': 1. Get received withdrawals from exchange')
    list_of_assets = []
    for account_collection in firefly_account_collections:
        list_of_assets.append(account_collection.security)
    withdrawals = exchange_interface.get_withdrawals(from_timestamp, to_timestamp, list_of_assets)

    if len(withdrawals) == 0:
        print(trading_platform + ':   No new withdrawals found.')
        return

    print(trading_platform + ": 2. Import withdrawals to Firefly III")
    firefly_wrapper.import_withdrawals(withdrawals, firefly_account_collections, trading_platform)


def handle_interests(from_timestamp, to_timestamp, init, trading_platform, exchange_interface,
                     firefly_account_collections, epochs_to_calculate):
    if init:
        header_log = trading_platform + ': Importing all historical interests from ' + str(from_timestamp) + " to " + str(to_timestamp)
    else:
        header_log = trading_platform + ': Importing interests from ' + str(from_timestamp) + " to " + str(to_timestamp) + ", " + str(epochs_to_calculate) + " intervals."
    if config.debug:
        print(header_log)

    print(trading_platform + ': 1. Get received interest from savings from exchange')
    list_of_assets = []
    for account_collection in firefly_account_collections:
        list_of_assets.append(account_collection.security)
    received_interests = exchange_interface.get_savings_interests(from_timestamp, to_timestamp, list_of_assets)

    if len(received_interests) == 0:
        print(trading_platform + ':   No new interest received.')
        return

    print(trading_platform + ": 2. Import received interest to Firefly III")
    firefly_wrapper.import_received_interests(received_interests, firefly_account_collections, trading_platform)


def handle_trades(from_timestamp, to_timestamp, init, trading_platform, exchange_interface):
    epochs_to_calculate = get_epochs_differences(from_timestamp, to_timestamp, config.sync_inverval)
    if init:
        header_log = trading_platform + ': Importing all historical trades from ' + str(from_timestamp) + " to " + str(to_timestamp)
    else:
        header_log = trading_platform + ': Importing trades from ' + str(from_timestamp) + " to " + str(to_timestamp) + ", " + str(epochs_to_calculate) + " intervals."
    if config.debug:
        print(header_log)

    print(trading_platform + ': 1. Get eligible symbols from existing asset accounts within Firefly III')
    list_of_trading_pairs = exchange_interface.get_trading_pairs(
        firefly_wrapper.get_symbols_and_codes(trading_platform))

    print(trading_platform + ': 2. Get trades from crypto currency exchange')
    list_of_trade_data = exchange_interface.get_trades(from_timestamp, to_timestamp, list_of_trading_pairs)
    firefly_account_collections = firefly_wrapper.get_firefly_account_collections_for_pairs(list_of_trading_pairs,
                                                                                            trading_platform)
    if len(list_of_trade_data) == 0:
        print(trading_platform + ":   No trades to import.")
        are_transactions_to_import = False
    else:
        are_transactions_to_import = True
    if are_transactions_to_import:
        print(trading_platform + ': 4. Map transactions to Firefly III accounts and prepare import')
        new_transaction_collections = get_transaction_collections_from_trade_data(list_of_trade_data)
        augment_transaction_collections_with_firefly_accounts(new_transaction_collections, firefly_account_collections)
        print(trading_platform + ': 5. Import new trades as transactions to Firefly III')
        firefly_wrapper.import_transaction_collections(new_transaction_collections, trading_platform)
        print(trading_platform + ": 6. Finish import and going to sleep")

    return firefly_account_collections, epochs_to_calculate


def get_x_pub_of_account(account, expression):
    try:
        [result] = re.findall(expression, account.attributes.notes)
    except:
        pass
    return result


def get_transactions_from_blockchain(firefly_transactions, supported_blockchains):
    result = {}
    for supported_blockchain in supported_blockchains:
        client = supported_blockchains.get(supported_blockchain)
        for firefly_transaction in firefly_transactions:
            [inner_transaction] = firefly_transaction.attributes.transactions
            if inner_transaction.currency_code == client.get_currency_code() or inner_transaction.currency_symbol == client.get_currency_code():
                ledger_transaction = client.get_transaction_from_ledger(inner_transaction.external_id)
                result.setdefault(inner_transaction.external_id, {"firefly": firefly_transaction, "ledger": ledger_transaction, "code": client.get_currency_code()})
    return result


def handle_unclassified_transactions(trading_platform):
    # 1. get accounts with xPub in notes and get addresses from xPub
    supported_blockchains = {}
    for explorer_module in available_explorer:
        supported_blockchains.setdefault(explorer_module.get_blockchain_name(), explorer_module.get_blockchain_explorer())
    account_collections = [
        firefly_wrapper.create_firefly_account_collection(security, trading_platform)
        for security in supported_blockchains.keys()
    ]
    account_address_mapping = {}
    for supported_blockchain in supported_blockchains:
        explorer = supported_blockchains.get(supported_blockchain)
        identifier = explorer.get_address_identifier()
        regular_expression = explorer.get_address_re()
        accounts = firefly_wrapper.get_firefly_accounts_for_crypto_currency(explorer.get_currency_code(), identifier)
        for account in accounts:
            x_pub_of_account = \
                get_x_pub_of_account(account, regular_expression)
            addresses = explorer\
                .get_tx_addresses_from_address(address=x_pub_of_account)
            account_address_mapping\
                .setdefault(account.attributes.name, {"addresses": addresses, "account": account.attributes, "code": explorer.get_currency_code()})
    # 2. get transactions with crypto-trades-firefly-iii:unclassified-transaction in notes
    firefly_transactions = firefly_wrapper.get_transactions("unclassified-transaction", supported_blockchains)
    transactions = get_transactions_from_blockchain(firefly_transactions, supported_blockchains)
    # 3. rewrite transactions in Firefly-III
    firefly_wrapper.rewrite_unclassified_transactions(transactions, account_address_mapping, account_collections, trading_platform)


def interval_processor(from_timestamp, to_timestamp, init, trading_platform):
    exchange_interface = exchange_interface_factory.get_specific_exchange_interface(trading_platform)

    firefly_account_collections, epochs_to_calculate = handle_trades(from_timestamp, to_timestamp, init, trading_platform, exchange_interface)
    handle_interests(from_timestamp, to_timestamp, init, trading_platform, exchange_interface, firefly_account_collections, epochs_to_calculate)
    handle_withdrawals(from_timestamp, to_timestamp, init, trading_platform, exchange_interface, firefly_account_collections, epochs_to_calculate)
    handle_deposits(from_timestamp, to_timestamp, init, trading_platform, exchange_interface, firefly_account_collections, epochs_to_calculate)
    handle_unclassified_transactions(trading_platform)

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
