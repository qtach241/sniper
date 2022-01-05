import queue
from queue import Empty

class CostBasis(object):
    """
    Utility class which keeps track of cost basis. Only supports buys currently.
    """
    def __init__(self) -> None:
        self._fifo = queue.Queue()
        #self._lifo = queue.LifoQueue()

    def clear(self):
        try:
            while True:
                self._fifo.get_nowait()
        except Empty:
            pass

    def buy(self, qty, price):
        b = { 'qty' : qty, 'price' : price }
        self._fifo.put(b)
    
    def sell(self, qty, price):
        pass

    def get_cost_basis(self):
        cb = 0
        cum = 0
        for i in self._fifo.queue:
            cb = ((cum * cb) + (i['qty'] * i['price'])) / (cum + i['qty'])
            cum += i['qty']
        return cb


if __name__ == '__main__':
    # Sanity check
    cb = CostBasis()

    cb.buy(200, 175)
    print(cb.get_cost_basis())
    cb.buy(1000, 190)
    print(cb.get_cost_basis())
    cb.buy(500, 205)
    print(cb.get_cost_basis())

    cb.clear()
