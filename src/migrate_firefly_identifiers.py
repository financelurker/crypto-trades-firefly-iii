import firefly_iii_client
import config
from src.firefly import firefly_wrapper

LEGACY_ASSET_ACCOUNT_IDENTIFIER = "py1binance2firefly3:binance-fund"
LEGACY_REVENUE_ACCOUNT_IDENTIFIER = "py1binance2firefly3:binance-interest"
LEGACY_EXPENSE_ACCOUNT_IDENTIFIER = "py1binance2firefly3:binance-fees"
LEGACY_TRADE_TRANSACTION_IDENTIFIER = "py1binance2firefly3:binance-fund"
LEGACY_FEE_TRANSACTION_IDENTIFIER = "py1binance2firefly3:binance-fund"


def migrate_identifiers():
    firefly_wrapper.connect()
    if config.debug:
        print("Migration: Checking if there are any account or transaction identifiers to migrate.")
    count_of_migrated_elements = 0
    count_of_migrated_elements += migrate_firefly_account_identifiers()
    count_of_migrated_elements += migrate_firefly_transaction_identifiers()
    if config.debug:
        print("Migration: " + str(count_of_migrated_elements) + " notes of accounts or transactions were migrated.\n")


def get_firefly_accounts():
    with firefly_iii_client.ApiClient(firefly_wrapper.firefly_config) as api_client:
        account_api = firefly_iii_client.AccountsApi(api_client)

        list_of_accounts = []
        try:
            list_of_all_accounts = account_api.list_account()
            for account_read in list_of_all_accounts.data:
                list_of_accounts.append(account_read)
        except Exception as e:
            print("Migration: Cannot get Firefly-III accounts." % e)
        return list_of_accounts


def migrate_identifiers_on_accounts(list_of_accounts):
    accounts_to_migrate = []
    for account in list_of_accounts:
        if str(LEGACY_ASSET_ACCOUNT_IDENTIFIER) in str(account.attributes.notes):
            account.attributes.notes = account.attributes.notes.replace(LEGACY_ASSET_ACCOUNT_IDENTIFIER, firefly_wrapper.get_acc_fund_key("binance"))
            accounts_to_migrate.append(account)
        elif str(LEGACY_EXPENSE_ACCOUNT_IDENTIFIER) in str(account.attributes.notes):
            account.attributes.notes = account.attributes.notes.replace(LEGACY_EXPENSE_ACCOUNT_IDENTIFIER, firefly_wrapper.get_acc_expenses_key("binance"))
            accounts_to_migrate.append(account)
        elif str(LEGACY_REVENUE_ACCOUNT_IDENTIFIER) in str(account.attributes.notes):
            account.attributes.notes = account.attributes.notes.replace(LEGACY_REVENUE_ACCOUNT_IDENTIFIER, firefly_wrapper.get_acc_revenue_key("binance"))
            accounts_to_migrate.append(account)
    return accounts_to_migrate


def save_migrated_accounts(list_of_accounts):
    with firefly_iii_client.ApiClient(firefly_wrapper.firefly_config) as api_client:
        account_api = firefly_iii_client.AccountsApi(api_client)

        try:
            for account in list_of_accounts:
                payload = {'notes': account.attributes.notes}
                account_api.update_account(account.id, payload)
        except Exception as e:
            print("Migration: Cannot update Firefly III accounts." % e)


def migrate_firefly_account_identifiers():
    firefly_accounts = get_firefly_accounts()
    migrated_accounts = migrate_identifiers_on_accounts(firefly_accounts)
    save_migrated_accounts(migrated_accounts)

    # get all accounts with "py1binance2firefly3:binance-fund"
    # replace to "crypto-trades-firefly-iii:binance:fund"

    # get all accounts with "py1binance2firefly3:binance-fees"
    # replace to "crypto-trades-firefly-iii:binance:expenses"

    # get all accounts with "py1binance2firefly3:binance-interest"
    # replace to "crypto-trades-firefly-iii:binance:revenue"
    return len(migrated_accounts)


def migrate_firefly_transaction_identifiers():
    # get all accounts with "py1binance2firefly3:binance-fee"
    # replace to "crypto-trades-firefly-iii:binance:fee"

    # get all accounts with "py1binance2firefly3:binance-trade"
    # replace to "crypto-trades-firefly-iii:binance:trade"
    return 0
