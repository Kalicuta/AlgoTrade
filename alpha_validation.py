import os
import glob
import copy

from pipeline import *


class DelphaDataClean(DataClean):
    def __init__(self, raw_data):
        DataClean.__init__(self, raw_data)

    def data_cleansing(self):
        i = 1
        for f in self.raw_data.path:
            try:
                df = pd.read_csv(f, header=0)
                df.columns = self.raw_data.columns
                df = df[["date", "time", "symbol", "midPrice", "bookAlpha", "tradeAlpha"]]   # additional
                df = df.dropna()
                df = df.set_index(['symbol'])
                df.date = pd.to_datetime(df.date, format=self.raw_data.date_format)
                df.time = pd.to_datetime(df.time, format=self.raw_data.time_format).dt.time
            except ValueError:
                print 'Raw data cleansing error!'

            # print to screen (optional)
            date = df.head(1)['date'][0].date()

            data_set = []
            grouped_by_symbol = df.groupby(level='symbol')
            for symbol, data in grouped_by_symbol:
                data = data.sort_values('time')

                # Filtering (optional)
                data = data[data.midPrice > 0]
                data = data[data.midPrice < 200000]

                # Calculate returns using close or mid-price data
                for freq in [1]:
                    data['return'] = data.midPrice.shift(-freq)/data.midPrice - 1

                # Calculate alpha
                # data[self.alpha.name] = (data.close - data['open']) / ((data.high - data.low) + .001)

                data_set.append(data)

            # Save cleaned data
            # pd.concat(data_set).to_csv('cleaned_data/%s.csv' % date, sep=',')

            print i, date
            i += 1

        print 'Data Cleansing Done.'


def load_data(data):
    df_list = []
    for f in data.path:
        df = pd.read_csv(f, header=0, sep=',')
        df = df[(df['time'] <= '15:00') & (df['bookAlpha'] != 0)]   # optional
        df_list.append(df)

    data.data = pd.concat(df_list)
    return data


if __name__ == "__main__":

    Delpha_raw_data = Data(
        stamp='2013',
        path=glob.glob(os.path.join(os.getcwd(), 'raw_data/*.csv')),
        columns=["date", "time", "symbol", "midPrice", "const", "sector", "industry", "bookAlpha", "tradeAlpha",
                 "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"],
        date_format='%Y%m%d',
        time_format='%H%M%S.0'
    )

    Delpha_clean_data = copy.deepcopy(Delpha_raw_data)
    Delpha_clean_data.path = glob.glob(os.path.join(os.getcwd(), 'cleaned_data/*.csv'))

    Delpha_alpha = Alpha(name='bookAlpha', horizon='minute')

    # DelphaDataClean(Delpha_raw_data).data_cleansing()
    Delpha_data = load_data(Delpha_clean_data)
    AlphaValidation(Delpha_data, Delpha_alpha, bin_num=20).analysis()
