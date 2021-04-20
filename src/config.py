import os


def get_boolean_from_default_true(os, env_var_name):
    env_var = os.environ[env_var_name]
    return not env_var.lower() in 'false'


def get_boolean_from_default_false(os, env_var_name):
    env_var = os.environ[env_var_name]
    return env_var.lower() in 'true'


firefly_host = os.environ['FIREFLY_HOST']
try:
    firefly_verify_ssl = get_boolean_from_default_true(os, 'FIREFLY_VALIDATE_SSL')
except Exception as e:
    firefly_verify_ssl = True
firefly_access_token = os.environ['FIREFLY_ACCESS_TOKEN']

try:
    binance_api_key = os.environ['BINANCE_API_KEY']
    binance_api_secret = os.environ['BINANCE_API_SECRET']
    binance_enabled = True
except Exception as e:
    binance_enabled = False

try:
    cryptocom_api_key = os.environ['CRYPTOCOM_API_KEY']
    cryptocom_api_secret = os.environ['CRYPTOCOM_API_SECRET']
    cryptocom_enabled = False
except Exception as e:
    cryptocom_api_key = "test"
    cryptocom_api_secret = "test"
    cryptocom_enabled = False

sync_begin_timestamp = os.environ['SYNC_BEGIN_TIMESTAMP']
sync_inverval = os.environ['SYNC_TRADES_INTERVAL']

try:
    debug = get_boolean_from_default_false(os, 'DEBUG')
except Exception as e:
    debug = False
