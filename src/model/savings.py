from datetime import datetime
from enum import Enum


class InterestData(object):
    def __init__(self, type, interest, interest_currency, date, due):
        self.type: SavingsType = type
        self.amount: str = interest
        self.currency: str = interest_currency
        self.date: datetime = date
        self.due: InterestDue = due


class InterestDue(Enum):
    DAILY = 1
    FIXED = 2
    ACTIVE = 99


class SavingsType(Enum):
    STAKING = 1
    LENDING = 2
