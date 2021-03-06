from __future__ import print_function

import datetime
import hashlib
from typing import List

import firefly_iii_client
import urllib3
from firefly_iii_client import ApiException

import config as config
from model.savings import InterestDue
from model.transaction import TransactionType
from model.withdrawal_deposit import WithdrawalData, DepositData


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


def get_withdrawal_unclassified_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":unclassified-transaction:" + trading_platform.lower()


def get_withdrawal_classified_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":" + trading_platform.lower()


def get_deposit_unclassified_key(trading_platform):
    return SERVICE_IDENTIFICATION + ":unclassified-transaction:" + trading_platform.lower()


def get_deposit_classified_key(trading_platform):
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

        asset_accounts = []

        try:
            accounts = []

            paging = True
            page = 1
            while paging:
                get_accounts_response = accounts_api.list_account(page=page)

                accounts.extend(get_accounts_response.data)

                if get_accounts_response.meta.pagination.total_pages > page:
                    page += 1
                else:
                    paging = False

            for account in accounts:
                if account.attributes.type == 'asset':
                    asset_accounts.append(account)

            list_of_symbols_and_codes = []
            relevant_accounts = []

            notes_identifier = get_acc_fund_key(trading_platform.lower())

            for account in asset_accounts:
                notes = account.attributes.notes
                if notes is not None:
                    if notes_identifier in notes:
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


def write_new_received_interest_as_transaction(received_interest, account_collection, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []

        currency_code = account_collection.asset_account.attributes.currency_code
        currency_symbol = account_collection.asset_account.attributes.currency_symbol
        amount = received_interest.amount
        description = trading_platform + " | INTEREST | Currency: " + currency_code

        if received_interest.due == InterestDue.DAILY:
            description += " | Daily interest"
        elif received_interest.due == InterestDue.ACTIVE:
            description += " | Active interest"
        elif received_interest.due == InterestDue.FIXED:
            description += " | Locked interest"

        tags = [trading_platform.lower()]
        if config.debug:
            tags.append('dev')

        split = firefly_iii_client.TransactionSplit(
            amount=amount,
            date=received_interest.date,
            description=description,
            type='deposit',
            tags=tags,
            reconciled=True,
            source_name=account_collection.revenue_account.attributes.name,
            source_type=account_collection.revenue_account.attributes.type,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            destination_name=account_collection.asset_account.attributes.name,
            destination_type=account_collection.asset_account.attributes.type,
#            external_id=transaction_collection.trade_data.id,
            notes=get_acc_revenue_key(trading_platform)
        )
        split.import_hash_v2 = hash_transaction(split.amount, split.date, split.description, "", split.source_name, split.destination_name, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Writing a new received interest.')
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate received interest detected.')
            else:
                message: str = trading_platform + ':   - There was an unknown error writing a new received interest.'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error writing a new received interest.'
            if config.debug:
                print(message % e)
            else:
                print(message)


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


def hash_unclassifiable(amount, date, external_id, trading_platform: str, currency_code: str, tags: List[str]):
    hashed_result = str(amount) + str(date) + str(external_id) + trading_platform + currency_code
    for tag in tags:
        hashed_result += tag
    hash_object = hashlib.sha256(hashed_result.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig


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
        description = transaction_collection.trade_data.trading_platform + ' | ' + type_string + " | Security: " + transaction_collection.trade_data.trading_pair.security + " | Currency: " + transaction_collection.trade_data.trading_pair.currency + " | Ticker " + transaction_collection.trade_data.trading_pair.security + transaction_collection.trade_data.trading_pair.currency
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


def get_accounts_from_firefly(supported_blockchain, account_type, notes_keywords):
    result = []
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        # Create an instance of the API class
        accounts_api = firefly_iii_client.AccountsApi(api_client)
        try:
            accounts = []
            page = 0
            load_again = True
            while load_again:
                new_accounts = accounts_api.list_account(page=page).data
                accounts.extend(new_accounts)
                if len(new_accounts) < 50:
                    load_again = False
                else:
                    page += 1

            for account in accounts:
                if account.attributes.type == account_type and \
                        account.attributes.notes is not None and \
                        notes_keywords in account.attributes.notes and \
                        (account.attributes.currency_code == supported_blockchain or
                         account.attributes.currency_symbol == supported_blockchain):
                    result.append(account)
        except Exception as e:
            message = 'There was an error getting the accounts from Firefly III'
            if config.debug:
                print(message % e)
            else:
                print(message)
            exit(-604)
    return result


def get_transactions(notes_keyword, supported_blockchains):
    result = []
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        try:
            transactions = []
            page = 0
            load_next = True
            while load_next:
                next_transactions = transaction_api.list_transaction(type="all", page=page).data
                transactions.extend(next_transactions)
                if len(next_transactions) < 50:
                    load_next = False
                else:
                    page += 1
            for transaction in transactions:
                for inner_transaction in transaction.attributes.transactions:
                    if inner_transaction.notes is not None and \
                            notes_keyword in inner_transaction.notes and \
                            (any(inner_transaction.currency_code == supported_blockchains.get(s).get_currency_code() for s in supported_blockchains) or
                             any(inner_transaction.currency_symbol == supported_blockchains.get(s).get_currency_code() for s in supported_blockchains)):
                        result.append(transaction)
                        break
        except Exception as e:
            message = 'There was an error getting the transactions from Firefly III'
            if config.debug:
                print(message % e)
            else:
                print(message)
            exit(-604)
    return result


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


def get_firefly_accounts_for_crypto_currency(supported_blockchain, identifier):
    return get_accounts_from_firefly(supported_blockchain, 'asset', identifier)


def get_asset_account_for_security(security, trading_platform):
    return get_account_from_firefly(security, 'asset', get_acc_fund_key(trading_platform))


def get_expense_account_for_security(security, trading_platform):
    return get_account_from_firefly(None, 'expense', get_acc_expenses_key(trading_platform))


def get_revenue_account_for_security(security, trading_platform):
    return get_account_from_firefly(None, 'revenue', get_acc_revenue_key(trading_platform))


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


def import_received_interests(received_interests, firefly_account_collections, trading_platform):
    for received_interest in received_interests:
        for account_collection in firefly_account_collections:
            if received_interest.currency == account_collection.security:
                write_new_received_interest_as_transaction(received_interest, account_collection, trading_platform)


def write_new_withdrawal(withdrawal, account_collection, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []
        currency_code = account_collection.asset_account.attributes.currency_code
        currency_symbol = account_collection.asset_account.attributes.currency_symbol
        amount = withdrawal.amount
        tags = [trading_platform.lower()]
        description = trading_platform + " | WITHDRAWAL (unclassified) | Security: " + withdrawal.asset
        if config.debug:
            tags.append('dev')

        split = firefly_iii_client.TransactionSplit(
            amount=amount,
            date=datetime.datetime.fromtimestamp(int(withdrawal.timestamp / 1000)),
            description=description,
            type='withdrawal',
            tags=tags,
            reconciled=True,
            source_name=account_collection.asset_account.attributes.name,
            source_type=account_collection.asset_account.attributes.type,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            destination_name=account_collection.expense_account.attributes.name,
            destination_type=account_collection.expense_account.attributes.type,
            external_id=withdrawal.transaction_id,
            notes=get_withdrawal_unclassified_key(trading_platform)
        )
        split.import_hash_v2 = hash_unclassifiable(split.amount, split.date, split.external_id, trading_platform, currency_code, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Writing a new withdrawal.')
            # pprint(new_transaction)
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate withdrawal transaction detected. Here\'s the transaction id: "' + str(
                    withdrawal.transaction_id) + '"')
            else:
                message: str = trading_platform + ':   - There was an unknown error writing a new withdrawal. Here\'s the transaction id: "' + str(withdrawal.transaction_id) + '"'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error writing a new withdrawal. Here\'s the transaction id: "' + str(
                withdrawal.transaction_id) + '"'
            if config.debug:
                print(message % e)
            else:
                print(message)


def import_withdrawals(withdrawals: List[WithdrawalData], firefly_account_collections, trading_platform):
    for withdrawal in withdrawals:
        for account_collection in firefly_account_collections:
            if withdrawal.asset == account_collection.security:
                write_new_withdrawal(withdrawal, account_collection, trading_platform)


def write_new_deposit(deposit: DepositData, account_collection, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []
        currency_code = account_collection.asset_account.attributes.currency_code
        currency_symbol = account_collection.asset_account.attributes.currency_symbol
        amount = deposit.amount
        tags = [trading_platform.lower()]
        description = trading_platform + " | DEPOSIT (unclassified) | Security: " + deposit.asset
        if config.debug:
            tags.append('dev')

        split = firefly_iii_client.TransactionSplit(
            amount=amount,
            date=datetime.datetime.fromtimestamp(int(deposit.timestamp / 1000)),
            description=description,
            type='deposit',
            tags=tags,
            reconciled=True,
            source_name=account_collection.revenue_account.attributes.name,
            source_type=account_collection.revenue_account.attributes.type,
            currency_code=currency_code,
            currency_symbol=currency_symbol,
            destination_name=account_collection.asset_account.attributes.name,
            destination_type=account_collection.asset_account.attributes.type,
            external_id=deposit.transaction_id,
            notes=get_withdrawal_unclassified_key(trading_platform)
        )
        split.import_hash_v2 = hash_unclassifiable(split.amount, split.date, split.external_id, trading_platform, currency_code, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Writing a new deposit.')
            # pprint(new_transaction)
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate deposit transaction detected. Here\'s the trade id: "' + str(
                    deposit.transaction_id) + '"')
            else:
                message: str = trading_platform + ':   - There was an unknown error writing a new deposit. Here\'s the transaction id: "' + str(deposit.transaction_id) + '"'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error writing a new deposit. Here\'s the transaction id: "' + str(
                deposit.transaction_id) + '"'
            if config.debug:
                print(message % e)
            else:
                print(message)


def import_deposits(deposits, firefly_account_collections, trading_platform):
    for deposit in deposits:
        for account_collection in firefly_account_collections:
            if deposit.asset == account_collection.security:
                write_new_deposit(deposit, account_collection, trading_platform)


def get_relevant_firefly_deposit_account(transaction_data, account_address_mapping):
    for account_name in account_address_mapping:
        account_mapping = account_address_mapping.get(account_name)
        if not account_mapping.get("code") == transaction_data.get("firefly").attributes.transactions[0].currency_code and not account_mapping.get("code") == transaction_data.get("firefly").attributes.transactions[0].currency_symbol:
            continue
        for firefly_address in account_mapping.get("addresses"):
            for ledger_addresses in transaction_data.get("ledger").ins:
                if firefly_address == ledger_addresses:
                    return account_mapping
    return None


def get_relevant_firefly_withdrawal_account(transaction_data, account_address_mapping):
    for account_name in account_address_mapping:
        account_mapping = account_address_mapping.get(account_name)
        if not account_mapping.get("code") == transaction_data.get("firefly").attributes.transactions[0].currency_code and not account_mapping.get("code") == transaction_data.get("firefly").attributes.transactions[0].currency_symbol:
            continue
        for firefly_address in account_mapping.get("addresses"):
            for ledger_addresses in transaction_data.get("ledger").outs:
                if firefly_address == ledger_addresses:
                    return account_mapping
    return None


def rewrite_unclassified_deposit_transaction(transaction_data, relevant_firefly_account, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []

        [inner_transaction] = transaction_data.get("firefly").attributes.transactions

        tags = inner_transaction.tags
        if config.debug:
            tags.append('dev')
        description = trading_platform + " | DEPOSIT | Security: " + transaction_data.get("code")

        split = firefly_iii_client.TransactionSplit(
            amount=inner_transaction.amount,
            date=inner_transaction.date,
            description=description,
            type='transfer',
            tags=tags,
            reconciled=True,
            source_name=relevant_firefly_account.get("account").name,
            source_type=relevant_firefly_account.get("account").type,
            currency_code=inner_transaction.currency_code,
            currency_symbol=inner_transaction.currency_symbol,
            destination_name=inner_transaction.destination_name,
            destination_type=inner_transaction.destination_type,
            external_id=inner_transaction.external_id,
            notes=get_withdrawal_classified_key(trading_platform)
        )
        split.import_hash_v2 = hash_unclassifiable(float(split.amount), split.date, split.external_id, trading_platform, split.currency_code, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Rewriting a deposit.')
            transaction_api.delete_transaction(transaction_data.get("firefly").id)
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate deposit transaction detected. Here\'s the external id: "' + str(
                    inner_transaction.external_id) + '"')
            else:
                message: str = trading_platform + ':   - There was an unknown error rewriting a deposit. Here\'s the external id: "' + str(
                    inner_transaction.external_id) + '"'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error rewriting a deposit. Here\'s the external id: "' + str(
                inner_transaction.external_id) + '"'
            if config.debug:
                print(message % e)
            else:
                print(message)


def rewrite_unclassified_withdrawal_transaction(transaction_data, relevant_firefly_account, trading_platform):
    with firefly_iii_client.ApiClient(firefly_config) as api_client:
        transaction_api = firefly_iii_client.TransactionsApi(api_client)
        list_inner_transactions = []

        [inner_transaction] = transaction_data.get("firefly").attributes.transactions

        tags = inner_transaction.tags
        if config.debug:
            tags.append('dev')
        description = trading_platform + " | WITHDRAWAL | Security: " + transaction_data.get("code")

        split = firefly_iii_client.TransactionSplit(
            amount=inner_transaction.amount,
            date=inner_transaction.date,
            description=description,
            type='transfer',
            tags=tags,
            reconciled=True,
            source_name=inner_transaction.source_name,
            source_type=inner_transaction.source_type,
            currency_code=inner_transaction.currency_code,
            currency_symbol=inner_transaction.currency_symbol,
            destination_name=relevant_firefly_account.get("account").name,
            destination_type=relevant_firefly_account.get("account").type,
            external_id=inner_transaction.external_id,
            notes=get_withdrawal_classified_key(trading_platform)
        )
        split.import_hash_v2 = hash_unclassifiable(float(split.amount), split.date, split.external_id, trading_platform, split.currency_code, split.tags)
        list_inner_transactions.append(split)
        new_transaction = firefly_iii_client.Transaction(apply_rules=False, transactions=list_inner_transactions, error_if_duplicate_hash=True)

        try:
            if config.debug:
                print(trading_platform + ':   - Rewriting a withdrawal.')
            transaction_api.delete_transaction(transaction_data.get("firefly").id)
            transaction_api.store_transaction(new_transaction)
        except ApiException as e:
            if e.status == 422 and "Duplicate of transaction" in e.body:
                print(trading_platform + ':   - Duplicate withdrawal transaction detected. Here\'s the external id: "' + str(
                    inner_transaction.external_id) + '"')
            else:
                message: str = trading_platform + ':   - There was an unknown error rewriting a withdrawal. Here\'s the external id: "' + str(
                    inner_transaction.external_id) + '"'
                if config.debug:
                    print(message % e)
                else:
                    print(message)
        except Exception as e:
            message: str = trading_platform + ':   - There was an unknown error rewriting a withdrawal. Here\'s the external id: "' + str(
                inner_transaction.external_id) + '"'
            if config.debug:
                print(message % e)
            else:
                print(message)


def rewrite_unclassified_transactions(transactions, account_address_mapping, account_collections, trading_platform):
    print("Rewriting " + str(len(transactions)) + " deposits/withdrawals.")
    for transaction in transactions:
        transaction_data = transactions.get(transaction)
        [inner_transaction] = transaction_data.get("firefly").attributes.transactions
        if trading_platform + " | DEPOSIT (unclassified) | Security: " in inner_transaction.description:
            relevant_firefly_account = get_relevant_firefly_deposit_account(transaction_data, account_address_mapping)
            rewrite_unclassified_deposit_transaction(transaction_data, relevant_firefly_account, trading_platform)
        elif trading_platform + " | WITHDRAWAL (unclassified) | Security: " in inner_transaction.description:
            relevant_firefly_account = get_relevant_firefly_withdrawal_account(transaction_data, account_address_mapping)
            rewrite_unclassified_withdrawal_transaction(transaction_data, relevant_firefly_account, trading_platform)
