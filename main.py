from collections import deque
from sortedcontainers import SortedDict
import sys
sys.stdout = open("output.txt", "w")
debug = True
class OrderBook:
    def __init__(self):
        self.bids = SortedDict(lambda x: -x)  # highest price first
        self.asks = SortedDict()              # lowest price first
        self.order_index = {}                  # order_id -> (side, price, order)

    # Internal helper to match one bid and one ask
    def _match_one(self, bid_queue, ask_queue):
        bid, ask = bid_queue[0], ask_queue[0]
        traded_qty = min(bid["qty"], ask["qty"])
        bid["qty"] -= traded_qty
        ask["qty"] -= traded_qty
        if debug:
            print(f"TRADE {traded_qty} at price {self.asks.peekitem()[0]}, SELLER ID: {ask['trader_id']}, BUYER ID: {bid['trader_id']}, ASK ID: {ask['id']}, BID ID: {bid['id']}")
        else:
            print(f"TRADE {traded_qty} at price {self.asks.peekitem()[0]}")
        if bid["qty"] == 0:
            #print(f"Filled bid order: {bid['id']}")
            bid_queue.popleft()
        if ask["qty"] == 0:
            #print(f"Filled ask order: {ask['id']}")
            ask_queue.popleft()

    # Match as many orders as possible
    def match_orders(self):
        while self.bids and self.asks:
            best_bid_price, bid_queue = self.bids.peekitem(0)
            best_ask_price, ask_queue = self.asks.peekitem(0)
            if best_bid_price < best_ask_price:
                break
            self._match_one(bid_queue, ask_queue)
            if not bid_queue:
                self.bids.pop(best_bid_price)
            if not ask_queue:
                self.asks.pop(best_ask_price)

    # Add a limit order to the book
    def add_limit_order(self, order_id, side, price, qty, trader_id):
        price = float(price)
        qty = float(qty)
        book = self.bids if side.upper() == "BUY" else self.asks
        order = {"id": order_id, "qty": qty, "trader_id": trader_id}
        book.setdefault(price, deque()).append(order)
        self.order_index[order_id] = (side.upper(), price, order)
        self.match_orders()

    # Add a market order
    def add_market_order(self, order_id, qty, trader_id, side):
        qty = float(qty)
        filled_qty = 0
        if debug:
            print(f"Starting to fill market order id: {order_id}")
        if side == "BUY":
            while qty > 0 and self.asks:
                best_ask_price, ask_queue = self.asks.peekitem(0)
                while ask_queue and qty > 0:
                    ask_order = ask_queue[0]
                    trade_qty = min(qty, ask_order["qty"])
                    ask_order["qty"] -= trade_qty
                    qty -= trade_qty
                    filled_qty += trade_qty
                    if debug:
                        print(f"TRADE {trade_qty} at price {best_ask_price}, SELLER ID: {ask_order['trader_id']}, BUYER ID: {trader_id}, ASK ID: {ask_order['id']}")
                    else:
                        print(f"TRADE {trade_qty} at price {best_ask_price}")

                    if ask_order["qty"] == 0:
                        ask_queue.popleft()

                if not ask_queue:
                    self.asks.pop(best_ask_price)

            if qty > 0:
                print(f"MARKET ORDER {order_id} NOT FULLY FILLED, REMAINING QTY: {qty}")
            elif debug:
                print(f"MARKET ORDER {order_id} FULLY FILLED")

        else:
            while qty > 0 and self.bids:
                best_bid_price, bid_queue = self.bids.peekitem(0)
                while bid_queue and qty > 0:
                    bid_order = bid_queue[0]
                    trade_qty = min(qty, bid_order["qty"])
                    bid_order["qty"] -= trade_qty
                    qty -= trade_qty
                    if debug:
                        print(f"TRADE {trade_qty} at price {best_bid_price}, SELLER ID: {trader_id}, BUYER ID: {bid_order['trader_id']}, BID ID: {bid_order['id']}")
                    else:
                        print(f"TRADE {trade_qty} at price {best_bid_price}")

                    if bid_order["qty"] == 0:
                        bid_queue.popleft()
                if not bid_queue:
                    self.bids.pop(best_bid_price)
            if qty > 0:
                print(f"MARKET ORDER {order_id} NOT FULLY FILLED, REMAINING QTY: {qty}")
            elif debug:
                print(f"MARKET ORDER {order_id} FULLY FILLED")
    # Cancel an existing order
    def cancel_order(self, order_id):
        if order_id not in self.order_index:
            print(f"Order {order_id} not found")
            return
        side, price, _ = self.order_index.pop(order_id)
        book = self.bids if side == "BUY" else self.asks
        book[price] = deque(o for o in book[price] if o["id"] != order_id)
        if not book[price]:
            del book[price]
        print(f"CANCEL {order_id}")

    # Placeholder for modify order
    def modify_order(self):
        pass


def main():
    my_book = OrderBook()
    # Use 'with' to ensure file is closed properly
    with open('events.csv') as my_file:
        lines = [line.strip().split(",") for line in my_file]

    for line in lines[1:]:
        event_type = line[1].upper()
        if event_type == "LIMIT_ADD":
            my_book.add_limit_order(line[2], line[3], line[4], line[5], line[6])
        elif event_type == "CANCEL":
            my_book.cancel_order(line[2])
        elif event_type == "MARKET":
            # Make sure the correct CSV columns match order_id, qty, trader_id
            my_book.add_market_order(line[2], line[5], line[6], line[3])


if __name__ == "__main__":
    main()
