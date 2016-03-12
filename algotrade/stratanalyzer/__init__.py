from datetime import datetime
import algotrade.tools


class Tick(object):
    def __init__(self, time, high, low, open_=.0, close_=.0):
        self.time = time
        self.high = high
        self.low = low
        self.open = open_
        self.close = close_


class Trade(object):
    def __init__(self, time, price, direction):
        self.time = time
        self.price = price
        self.direction = direction


def create_trade(record):
    direction = record['Direction']
    price = float(record['Price'])
    time = datetime.strptime(record['Timestamp'], '%Y-%m-%d %H:%M:%S')
    return Trade(time, price, direction)


def create_tick(record):
    high = float(record['High'])
    low = float(record['Low'])
    open_ = float(record['Open'])
    close_ = float(record['Close'])
    time = algotrade.tools.string_to_time(record['Date'], record['Time'])
    tick = Tick(time, high, low, open_, close_)
    return tick
