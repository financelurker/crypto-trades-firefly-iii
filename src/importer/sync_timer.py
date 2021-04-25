import config as config
import datetime
import importer.sync_logic as sync_logic
from exchanges.exchange_interface import ExchangeUnderMaintenanceException


class SyncTimer(object):
    last_sync_result = None
    last_sync_interval_begin_timestamp = None

    def initial_sync(self, trading_platform):
        print(trading_platform + ': Initializing trade import from crypto exchange to Firefly III')
        begin_of_sync_timestamp = config.sync_begin_timestamp
        try:
            self.last_sync_interval_begin_timestamp = self.import_all_from_exchange(begin_of_sync_timestamp,
                                                                                    trading_platform)
        except ExchangeUnderMaintenanceException as maintenance:
            print("Exchange under maintenance. Delaying import of all trades.")
            self.last_sync_interval_begin_timestamp = datetime.datetime.fromisoformat(begin_of_sync_timestamp)\
                                                          .timestamp() * 1000
        self.last_sync_result = 'ok'
        return

    def sync(self, trading_platform):
        if self.last_sync_interval_begin_timestamp is None:
            print("SYNC: The sync was not initialized properly")
            exit(-700)
        if self.last_sync_result is None or not str(self.last_sync_result).lower() == 'ok':
            print("SYNC: The last sync did not finish successful: " + str(self.last_sync_result))
            exit(-700)

        config_sync_interval = config.sync_inverval
        self.sync_interval(self.last_sync_interval_begin_timestamp, config_sync_interval, trading_platform)

    def sync_interval(self, begin_timestamp_in_millis, interval, trading_platform):
        current_datetime = datetime.datetime.now()

        print(trading_platform + ": Now: " + str(datetime.datetime.now()))
        print(trading_platform + ": Last Interval Begin: " + str(datetime.datetime.fromtimestamp(begin_timestamp_in_millis / 1000)))

        previous_last_sync_interval_begin_timestamp = self.last_sync_interval_begin_timestamp
        new_to_timestamp_in_millis = self.get_last_interval_begin_millis(config.sync_inverval, current_datetime)

        try:
            self.last_sync_result = sync_logic.interval_processor(previous_last_sync_interval_begin_timestamp, new_to_timestamp_in_millis, False, trading_platform)
            self.last_sync_interval_begin_timestamp = new_to_timestamp_in_millis
        except ExchangeUnderMaintenanceException as maintenance:
            print("Exchange under maintenance. Skipping interval processing.")

    def get_last_interval_begin_millis(self, interval, current_datetime):
        if interval == 'hourly':
            epoch_counter = int(current_datetime.timestamp() / (60 * 60))
            last_epoch = epoch_counter - 1
            return last_epoch * 60 * 60 * 1000
        elif interval == 'daily':
            epoch_counter = int(current_datetime.timestamp() / (60 * 60 * 24))
            last_epoch = epoch_counter - 1
            return last_epoch * 60 * 60 * 24 * 1000
        elif interval == 'debug':
            epoch_counter = int(current_datetime.timestamp() / 10)
            return epoch_counter * 10 * 1000
        else:
            print("The configured interval is not supported. Use 'hourly' or 'daily' within your config.")
            exit(-749)

    def import_all_from_exchange(self, begin_of_sync_timestamp, trading_platform):
        current_datetime = datetime.datetime.now()
        to_timestamp = self.get_last_interval_begin_millis(config.sync_inverval, current_datetime)
        begin_timestamp = int(datetime.datetime.fromisoformat(config.sync_begin_timestamp).timestamp() * 1000)
        sync_logic.interval_processor(begin_timestamp, to_timestamp, True, trading_platform)
        return to_timestamp

