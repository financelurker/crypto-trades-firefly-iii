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

sync_begin_timestamp = os.environ['SYNC_BEGIN_TIMESTAMP']
sync_inverval = os.environ['SYNC_TRADES_INTERVAL']

try:
    enc_read = os.environ['DEBUG']
    debug = True
except Exception as e:
    debug = False
