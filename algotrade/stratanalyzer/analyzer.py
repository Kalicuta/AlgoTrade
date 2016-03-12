import csv
from datetime import datetime
from itertools import izip_longest
from operator import truediv
import algotrade.stratanalyzer

DIRECTION_BUY = '0'
DIRECTION_SELL = '1'


class GeneralAnalyzer(object):
    def __init__(self, raw_trades):
        self.input_data_file = open('TF1min.csv', 'rb')
        self.input_trade_file = open(raw_trades, 'rb')

        self.__tickList = []
        tick_data = csv.DictReader(self.input_data_file)
        for tick in tick_data:
            self.__tickList.append(algotrade.stratanalyzer.create_tick(tick))

        self.__tradeList = []
        trade_data = csv.DictReader(self.input_trade_file)
        for trade in trade_data:
            self.__tradeList.append(algotrade.stratanalyzer.create_trade(trade))

        print 'total bars:\t', len(self.__tickList)
        print 'total trades:\t', len(self.__tradeList)

        self.output_trades_file = open('all_trades.csv', 'wb')
        self.__tradeSummaryWriter = csv.writer(self.output_trades_file)
        self.__tradeSummaryWriter.writerow(['Trade Index',
                                            'Entry Time', 'Entry Price', 'Entry Direction',
                                            'Exit Time', 'Exit Price',
                                            'MFE', 'MFE Time', 'MAE', 'MAE Time',
                                            'Profit'])

        self.output_series_file = open('time_series.csv', 'wb')
        self.__outputSeriesWriter = csv.writer(self.output_series_file)
        self.__outputSeriesWriter.writerow(['Datetime',
                                            'Open', 'High', 'Low', 'Close',
                                            'Entry Price', 'Entry Time', 'Exit Price', 'Exit Time',
                                            'Trade Index', 'Trade Type',
                                            'UnrealizedPnL'])

        # for current trade
        self.__entry = None
        self.__exit = None
        self.__mfe = None
        self.__mae = None
        self.__mfeTime = None
        self.__maeTime = None

        # for all trades
        self.__profitList = []
        self.__mfeList = []
        self.__maeList = []

        # trade ID seed
        self.__tradeID = 0

    def __next_trade(self):
        self.__tradeID += 1

        if self.__exit.price > self.__entry.price and self.__entry.direction == DIRECTION_BUY \
                or self.__exit.price < self.__entry.price and self.__entry.direction == DIRECTION_SELL:
            self.__profitList.append(abs(self.__exit.price - self.__entry.price))
        else:
            self.__profitList.append(0 - abs(self.__exit.price - self.__entry.price))

        self.__maeList.append(0 - self.__mae)
        self.__mfeList.append(self.__mfe)

        row = [str(self.__tradeID),
               str(self.__entry.time),
               str(self.__entry.price),
               'B' if self.__entry.direction == DIRECTION_BUY else 'S',
               str(self.__exit.time),
               str(self.__exit.price),
               str(self.__mfe),
               str(self.__mfeTime),
               str(self.__mae),
               str(self.__maeTime),
               str(self.__exit.price - self.__entry.price) if self.__entry.direction == DIRECTION_BUY
               else str(self.__entry.price - self.__exit.price)
               ]
        self.__tradeSummaryWriter.writerow(row)

    def __close(self):
        self.input_data_file.close()
        self.input_trade_file.close()
        self.output_trades_file.close()
        self.output_series_file.close()

    def start(self):

        index = 0

        for tick in self.__tickList:
            if self.__entry is None and self.__exit is None:
                self.__entry = self.__tradeList[index]
                self.__exit = self.__tradeList[index + 1]
                self.__mfe = 0
                self.__mae = 0
                self.__mfeTime = self.__entry.time
                self.__maeTime = self.__entry.time
                index += 1
                if index + 1 >= len(self.__tradeList):
                    print "Reached end of trade list."
                    self.__close()
                    return

            if self.__entry.time <= tick.time <= self.__exit.time:
                self.__outputSeriesWriter.writerow([tick.time,
                                                    tick.open, tick.high, tick.low, tick.close,
                                                    self.__entry.price, self.__entry.time,
                                                    self.__exit.price, self.__exit.time,
                                                    index,
                                                    'Long' if self.__entry.direction == DIRECTION_BUY else 'Short',
                                                    self.__exit.price - tick.close
                                                    if self.__entry.direction == DIRECTION_BUY
                                                    else tick.close - self.__exit.price,
                                                    tick.time - self.__exit.time])

                if self.__entry.direction == DIRECTION_BUY:
                    if tick.high - self.__entry.price > self.__mfe:
                        self.__mfe = tick.high - self.__entry.price
                        self.__mfeTime = tick.time
                    if self.__entry.price - tick.low > self.__mae:
                        self.__mae = self.__entry.price - tick.low
                        self.__maeTime = tick.time
                elif self.__entry.direction == DIRECTION_SELL:
                    if self.__entry.price - tick.low > self.__mfe:
                        self.__mfe = self.__entry.price - tick.low
                        self.__mfeTime = tick.time
                    if tick.high - self.__entry.price > self.__mae:
                        self.__mae = tick.high - self.__entry.price
                        self.__maeTime = tick.time
            if tick.time == self.__exit.time:
                self.__next_trade()
                self.__entry = None
                self.__exit = None

        self.__close()


class HoldingAnalyzer(object):
    def __init__(self):
        self.__input_file = open('time_series.csv', 'rb')
        self.__tradeSummary = csv.DictReader(self.__input_file)
        self.__output_file = open('holding.csv', 'wb')
        self.__holdingOutputWriter = csv.writer(self.__output_file)

        self.__list_time_stamp = []
        self.__list_position = []
        self.__list_realized_price = []
        self.__list_trade_index = []
        self.__list_floating_profit = []
        self.__trade_log = []

        for row in self.__tradeSummary:
            self.__list_position.append(row['Trade Type'])
            self.__list_trade_index.append(int(row['Trade Index']))
            self.__list_floating_profit.append(float(row['UnrealizedPnL']))
            self.__list_time_stamp.append(datetime.strptime(row['Datetime'], '%Y-%m-%d %H:%M:%S'))

        self.__holding_sum_list = []
        self.__holding_count_list = []
        self.__holding_average_list = []
        self.__holding_std_list = []

    def start(self):
        self.__create_trade_book()
        self.__get_holding_period()
        self.__output()
        self.__input_file.close()
        self.__output_file.close()

    def __add_trade(self, details):
        new_trade = {
            # 'EntryDateTime': self.__list_time_stamp[k],
            # 'Position': pos,
            # 'EntryPrice': entry_price,
            # 'ExitPrice': exit_price,
            'Details': details,
            'Length': len(details)
        }
        self.__trade_log.append(new_trade)

    def __create_trade_book(self):
        details = []
        # print len(self.__list_time_stamp)
        for i in xrange(len(self.__list_time_stamp)):
            if i > 0 and self.__list_trade_index[i] != self.__list_trade_index[i-1]:
                self.__add_trade(details)
                details = []
            details.append(self.__list_floating_profit[i])

    def __get_holding_period(self):
        for trade in self.__trade_log:
            self.__holding_sum_list = [x+y for x, y in izip_longest(self.__holding_sum_list,
                                                                    trade['Details'], fillvalue=0)]
        trade_log_copy = self.__trade_log
        element = 0

        while True:
            for item in trade_log_copy:
                if item['Length'] > 0:
                    element += 1
                item['Length'] -= 1

            if element == 0:
                break
            self.__holding_count_list.append(element)
            element = 0

        self.__holding_average_list = map(truediv, self.__holding_sum_list, self.__holding_count_list)

        assert(len(self.__holding_sum_list) == len(self.__holding_count_list))

        sum_ = 0

        # Calculate standard deviation
        for i in xrange(len(self.__holding_average_list)):
            for trade in self.__trade_log:
                if i < len(trade['Details']):
                    # print trade['Details'][i]
                    temp = trade['Details'][i] - self.__holding_average_list[i]
                    sum_ += temp ** 2
            self.__holding_std_list.append((sum_/self.__holding_count_list[i]) ** .5)
            sum_ = 0
        # print self.__holding_std_list

    def __output(self):

        self.__holdingOutputWriter.writerow(['ResidualPnL', 'Count', 'Average', 'StdDev'])

        for i in xrange(len(self.__holding_count_list)):
            self.__holdingOutputWriter.writerow(
                [self.__holding_sum_list[i]] +
                [self.__holding_count_list[i]] +
                [self.__holding_average_list[i]] +
                [self.__holding_std_list[i]])
