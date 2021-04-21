from __future__ import print_function

import datetime
import hashlib

import firefly_iii_client
import urllib3
from firefly_iii_client import ApiException

import config as config
from model.transaction import TransactionType


class TransactionCollection(object):
    def __init__(self, trade_data, _from_ff_account, _to_ff_account, _commission_ff_account, _from_commission_account):
        self.trade_data = trade_data
        self.from_ff_account = _from_ff_account
        self.to_ff_account = _to_ff_account
        self.commission_account = _commission_ff_account
        self.from_commission_account = _from_commission_account


class FireflyAccountCollection(object):
    def __init__(self, security):
        self.security = security
        self.asset_account = None
        self.expense_account = None
        self.revenue_account = None

    def set_expense_account(self, _expense_account):
        self.expense_account = _expense_account

    def set_revenue_account(self, _revenue_account):
        self.revenue_account = _revenue_account

    def set_asset_account(self, _asset_account):
        self.asset_account = _asset_account


urllib3.disable_warnings()

firefly_config = None

SERVICE_IDENTIFICATION = "crypto-trades-firefly-iii"


def get_acc_fund_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":" + trading_platform.lower()


def get_acc_revenue_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":" + trading_platform.lower()


def get_acc_expenses_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":" + trading_platform.lower()


def get_tr_trade_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":" + trading_platform.lower()


def get_tr_fee_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":" + trading_platform.lower()


def connect():
    global firefly_config
    if firefly_config is not None:
        return True

    try:
        print('--------------------------------------------------------')
        print('Trying to connect to your Firefly III account...')

        firefly_iii_client.configuration.verify_ssl = False

        configuration = firefly_iii_client.configuration.Configuration(
            host=config.firefly_host
        )

        configuration.verify_ssl = config.firefly_verify_ssl
        configuration.access_token = config.firefly_access_token

        with firefly_iii_client.ApiClient(configuration) as api_client:
            try:
                firefly_iii_client.AboutApi(api_client).get_about()
            except Exception as e:
                raise Exception

        print('Connection to your Firefly III account established.')
        print('--------------------------------------------------------')
        firefly_config = configuration
        return True
    except Exception as e:
        if config.debug:
            print("Cannot get data from server. Check the connection or your access token configuration." % e)
        else:
            print("Cannot get data from server. Check the connection or your access token configuration.")
        exit(-600)


def get_symbols_and_codes(trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        # Create an instance of the API class
        accounts_api = firefly_iii_client.AccountsApi(api_client)

        try:
            accounts = accounts_api.list_account().data

            list_of_symbols_and_codes = []
            relevant_accounts = []

            notes_identifier = get_acc_fund_key(trading_platform.lower())

            for account in accounts:
                if account.attributes.type == 'asset' and \
                        account.attributes.notes is not None and \
                        notes_identifier in account.attributes.notes:
                    relevant_accounts.append(account)

            if config.debug:
                print(trading_platform + ':   ' + str(relevant_accounts.__len__()) + " relevant accounts found within your Firefly III instance.")
                for relevant_account in relevant_accounts:
                    print(trading_platform + ":   - \"" + relevant_account.attributes.name + "\"")

            for account in relevant_accounts:
                if not any(account.attributes.currency_code in s for s in list_of_symbols_and_codes):
                    list_of_symbols_and_codes.append(account.attributes.currency_code)
                if not any(account.attributes.currency_symbol in s for s in list_of_symbols_and_codes):
                    list_of_symbols_and_codes.append(account.attributes.currency_symbol)

            return list_of_symbols_and_codes
        except Exception as e:
            if config.debug:
                print('There was an error getting the accounts' % e)
            else:
                print('There was an error getting the accounts')
            exit(-601)


def write_commission(transaction_collection, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []

        currency_code = transaction_collection.from_commission_account.currency_code
        currency_symbol = transaction_collection.from_commission_account.currency_symbol
        amount = transaction_collection.trade_data.commission_amount
        description = transaction_collection.trade_data.trading_platform + " | FEE | Currency: " + currency_code

        tags = [transaction_collection.trade_data.trading_platform.lower()]
        if config.debug:
            tags.append('dev')

        split = firefly_iii_client.TransactionSplit(
            amount=amount,
            date=datetime.datetime.fromtimestamp(int(transaction_collection.trade_data.time / 1000)),
            description=description,
            type='withdrawal',
            tags=tags,
            reconciled=True,
            source_name=transaction_collection.from_commission_account.name,
            source_type=transaction_collection.from_commission_account.type,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            destination_name=transaction_collection.commission_account.name,
            destination_type=transaction_collection.commission_account.type,
            external_id=transaction_collection.trade_data.id,
            notes=get_tr_fee_key(transaction_collection.trade_data.trading_platform)
        )
        split.import_hash_v2 = hash_transaction(split.amount, split.date, split.description, split.external_id, split.source_name, split.destination_name, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Writing a new paid commission.')
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate commission transaction detected. Here\'s the trade id: "' + str(
                    transaction_collection.trade_data.id) + '"')
            else:
                message: str = trading_platform + ':   - There was an unknown error writing a new trade. Here\'s the trade id: "' + str(
                    transaction_collection.trade_data.id) + '"'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error writing a new trade. Here\'s the trade id: "' + str(
                transaction_collection.trade_data.id) + '"'
            if config.debug:
                print(message % e)
            else:
                print(message)


def hash_transaction(amount, date, description, external_id, source_name, destination_name, tags):
    hashed_result = str(amount) + str(date) + description + str(external_id) + source_name + destination_name
    for tag in tags:
        hashed_result += tag
    hash_object = hashlib.sha256(hashed_result.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig


def write_new_transaction(transaction_collection, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []
        if transaction_collection.trade_data.type == TransactionType.BUY:
            type_string = "BUY"
        else:
            type_string = "SELL"

        if type_string == "BUY":
            currency_code = transaction_collection.from_ff_account.currency_code
            currency_symbol = transaction_collection.from_ff_account.currency_symbol
            foreign_currency_code = transaction_collection.to_ff_account.currency_code
            foreign_currency_symbol = transaction_collection.to_ff_account.currency_symbol
        else:
            currency_code = transaction_collection.from_ff_account.currency_code
            currency_symbol = transaction_collection.from_ff_account.currency_symbol
            foreign_currency_code = transaction_collection.to_ff_account.currency_code
            foreign_currency_symbol = transaction_collection.to_ff_account.currency_symbol

        amount = transaction_collection.trade_data.security_amount
        foreign_amount = float(transaction_collection.trade_data.currency_amount)
        tags = [transaction_collection.trade_data.trading_platform.lower()]
        description = transaction_collection.trade_data.trading_platform + ' | ' + type_string + " | Security: " + transaction_collection.trade_data.trading_pair.security + " | Currency: " + transaction_collection.trade_data.trading_pair.currency + " | Ticker " + transaction_collection.trade_data.trading_pair.pair
        if config.debug:
            tags.append('dev')

        split = firefly_iii_client.TransactionSplit(
            amount=amount,
            date=datetime.datetime.fromtimestamp(int(transaction_collection.trade_data.time / 1000)),
            description=description,
            type='transfer',
            tags=tags,
            reconciled=True,
            source_name=transaction_collection.from_ff_account.name,
            source_type=transaction_collection.from_ff_account.type,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            destination_name=transaction_collection.to_ff_account.name,
            destination_type=transaction_collection.to_ff_account.type,
            foreign_currency_code=foreign_currency_code,
            foreign_currency_symbol=foreign_currency_symbol,
            foreign_amount=foreign_amount,
            external_id=transaction_collection.trade_data.id,
            notes=get_tr_fee_key(transaction_collection.trade_data.trading_platform)
        )
        split.import_hash_v2 = hash_transaction(split.amount, split.date, split.description, split.external_id, split.source_name, split.destination_name, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Writing a new trade.')
            # pprint(new_transaction)
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate trade transaction detected. Here\'s the trade id: "' + str(
                    transaction_collection.trade_data.id) + '"')
            else:
                message: str = trading_platform + ':   - There was an unknown error writing a new trade. Here\'s the trade id: "' + str(transaction_collection.trade_data.id) + '"'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error writing a new trade. Here\'s the trade id: "' + str(
                transaction_collection.trade_data.id) + '"'
            if config.debug:
                print(message % e)
            else:
                print(message)


def get_account_from_firefly(security, account_type, notes_keywords):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        # Create an instance of the API class
        accounts_api = firefly_iii_client.AccountsApi(api_client)
        try:
            accounts = accounts_api.list_account().data

            for account in accounts:
                if account.attributes.type == account_type and \
                        account.attributes.notes is not None and \
                        notes_keywords in account.attributes.notes:
                    if security is None:
                        return account
                    else:
                        if account.attributes.currency_code == security or account.attributes.currency_symbol == security:
                            return account
        except Exception as e:
            message = 'There was an error getting the accounts from Firefly III'
            if config.debug:
                print(message % e)
            else:
                print(message)
            exit(-604)
    return None


def get_asset_account_for_security(security, trading_platform):
    return get_account_from_firefly(security, 'asset', get_acc_fund_key(trading_platform))


def get_expense_account_for_security(security, trading_platform):
    return get_account_from_firefly(None, 'expense', get_acc_expenses_key(trading_platform))


def get_revenue_account_for_security(security, trading_platform):
    return get_account_from_firefly(security, 'revenue', get_acc_revenue_key(trading_platform))


def create_firefly_account_collection(security, trading_platform):
    result = FireflyAccountCollection(security)

    asset_account = get_asset_account_for_security(security, trading_platform)
    result.set_asset_account(asset_account)

    expense_account = get_expense_account_for_security(security, trading_platform)
    result.set_expense_account(expense_account)

    revenue_account = get_revenue_account_for_security(security, trading_platform)
    result.set_revenue_account(revenue_account)

    return result


def get_firefly_account_collections_for_pairs(list_of_trading_pairs, trading_platform):
    result = []

    relevant_securities = []
    for trading_pair in list_of_trading_pairs:
        if any(trading_pair.security in s for s in relevant_securities):
            continue
        relevant_securities.append(trading_pair.security)
    for trading_pair in list_of_trading_pairs:
        if any(trading_pair.currency in s for s in relevant_securities):
            continue
        relevant_securities.append(trading_pair.currency)
    for relevant_security in relevant_securities:
        result.append(create_firefly_account_collection(relevant_security, trading_platform))

    return result


def import_transaction_collection(transaction_collection, trading_platform):
    write_new_transaction(transaction_collection, trading_platform)
    write_commission(transaction_collection, trading_platform)


def import_transaction_collections(transaction_collections, trading_platform):
    for transaction_collection in transaction_collections:
        import_transaction_collection(transaction_collection, trading_platform)
