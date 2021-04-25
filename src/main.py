import time
from threading import Thread
import backends.exchanges as exchanges

import config
from backends.firefly import firefly_wrapper
import migrate_firefly_identifiers
from importer.sync_timer import SyncTimer


def start():
    migrate_firefly_identifiers.migrate_identifiers()
    try:
        impl_meta_class_instances = exchanges.get_impl_meta_class_instances()
        worker(impl_meta_class_instances)
    except Exception as e:
        if config.debug:
            print(str(e) % e)
        else:
            print(e)


def worker(meta_class_instances):
    if not firefly_wrapper.connect():
        exit(-12)

    interval_seconds = 0
    if config.sync_inverval == 'hourly':
        interval_seconds = 3600
    elif config.sync_inverval == 'daily':
        interval_seconds = 3600 * 24
    elif config.sync_inverval == 'debug':
        interval_seconds = 10
    else:
        print("The configured interval is not supported. Use 'hourly' or 'daily' within your config.")
        exit(-749)

    exchanges = []

    for meta_class in meta_class_instances:
        exchanges.append({
            'name': meta_class.get_exchange_name(),
            'timer_object': SyncTimer() if meta_class.is_enabled() else None
        })

    exchanges_available = False
    for exchange in exchanges:
        if exchange.get('timer_object') is not None:
            exchanges_available = True

    if not exchanges_available:
        print("There are no exchanges configured. Exit!")
        exit(0)

    for exchange in exchanges:
        if exchange.get('timer_object') is None:
            continue
        exchange.get('timer_object').initial_sync(exchange.get('name'))

    while True:
        time.sleep(interval_seconds)
        for exchange in exchanges:
            if exchange.get('timer_object') is None:
                continue
            trading_platform = exchange.get('name')
            exchange.get('timer_object').sync(trading_platform)


class MyThread(Thread):
    def __init__(self, event, trading_platform, timer_object):
        Thread.__init__(self)
        self.stopped = event
        self.trading_platform = trading_platform
        self.timer_object = timer_object

    def run(self):
        interval_seconds = 0
        if config.sync_inverval == 'hourly':
            interval_seconds = 3600
        elif config.sync_inverval == 'daily':
            interval_seconds = 3600 * 24
        elif config.sync_inverval == 'debug':
            interval_seconds = 10
        else:
            print("The configured interval is not supported. Use 'hourly' or 'daily' within your config.")
            exit(-749)
        while not self.stopped.wait(interval_seconds):
            self.timer_object.sync(self.trading_platform)


start()
