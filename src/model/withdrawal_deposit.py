class WithdrawalData(object):
    def __init__(self, trading_platform: str, amount: float, asset: str, target_address: str, timestamp: int, transaction_fee: float, transaction_id: str):
        self.trading_platform = trading_platform
        self.amount = amount
        self.asset = asset
        self.target_address = target_address
        self.timestamp = timestamp
        self.transaction_fee = transaction_fee
        self.transaction_id = transaction_id


class DepositData(object):
    def __init__(self, trading_platform: str, amount: float, asset: str, target_address: str, timestamp: int, transaction_id: str):
        self.trading_platform = trading_platform
        self.amount = amount
        self.asset = asset
        self.target_address = target_address
        self.timestamp = timestamp
        self.transaction_id = transaction_id
