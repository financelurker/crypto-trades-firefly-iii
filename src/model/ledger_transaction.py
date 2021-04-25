from typing import List


class LedgerTransaction:
    def __init__(self, txId: str, ins: List[str], outs: List[str]):
        self.txId = txId
        self.ins = ins
        self.outs = outs
