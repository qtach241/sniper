from abc import ABC, abstractmethod
from decimal import Decimal

BIN_DEPTH_MARKER = [0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20]

class L2OrderBook(ABC):

    ASK_LABELS = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']
    BID_LABELS = ['B9', 'B8', 'B7', 'B6', 'B5', 'B4', 'B3', 'B2', 'B1', 'B0']

    def get_ask_bins(self, ask):
        return [ask,
                ask+(ask*Decimal(BIN_DEPTH_MARKER[0])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[1])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[2])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[3])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[4])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[5])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[6])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[7])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[8])),
                ask+(ask*Decimal(BIN_DEPTH_MARKER[9]))]

    def get_bid_bins(self, bid):
        return [bid-(bid*Decimal(BIN_DEPTH_MARKER[9])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[8])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[7])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[6])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[5])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[4])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[3])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[2])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[1])),
                bid-(bid*Decimal(BIN_DEPTH_MARKER[0])),
                bid]

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def get_update_time(self):
        pass

    @abstractmethod
    def export(self):
        pass
