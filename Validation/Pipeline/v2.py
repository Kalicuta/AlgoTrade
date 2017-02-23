import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import copy
plt.style.use('ggplot')


class Data(object):
    def __init__(self, stamp='', path=None, columns=None, date_format=None, time_format=None):
        self.data = pd.DataFrame()
        self.stamp = stamp
        self.path = path
        self.columns = columns
        self.date_format = date_format
        self.time_format = time_format


class Alpha(object):
    def __init__(self, name='trial alpha'):
        self.name = name
        self.formula = None
        self.horizon = 'day'


class Analysis(object):
    def __init__(self, data, alpha):
        self.research_data = data
        self.alpha = alpha

    def analysis(self):
        raise NotImplementedError


class BinAnalysis(Analysis):
    def __init__(self, data, alpha, count=20):
        Analysis.__init__(self, data, alpha)
        self.num_of_bins = count
        self.alpha_return = pd.DataFrame()

    def _data_filtering(self):
        for f in self.research_data.path:
            df = pd.read_csv(f, header=0, sep=',')

            # Filter the input data
            df = df[df[self.alpha.name] != 0]

            self.research_data.data = self.research_data.data.append(df)

        self.research_data.data = self.research_data.data.dropna()
        self.research_data.data = self.research_data.data.sort_values(self.alpha.name)
        print 'Data Filtering Done.'

    def _create_alpha_return_df(self):
        list_of_df = np.array_split(self.research_data.data, self.num_of_bins)

        for df in list_of_df:
            alpha_bin = pd.DataFrame({
                self.alpha.name: [df[self.alpha.name].mean()],
                # choose different periods of returns
                'return': [df['return_1day'].mean() * 10000]
            })
            self.alpha_return = self.alpha_return.append(alpha_bin[[self.alpha.name, 'return']], ignore_index=True)
        print self.alpha_return.head(3)

    def _plot(self):
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        self.alpha_return['return'].plot(kind='bar', ax=ax1)
        ax2.plot(self.alpha_return[self.alpha.name], marker='o', ls='-', color='b')

        ax1.set_ylim((-10, 40))
        ax1.set_xlim((-1, 20))
        ax1.set_title(self.alpha.name+' - '+self.alpha.horizon)
        ax1.set_ylabel('Ave. return (bps)')
        ax1.legend(loc=2)

        ax2.set_ylim((-1, 1))
        ax2.set_ylabel('Ave. alpha')
        ax2.legend(loc=4)
        # ax1.set_xticklabels(self.alpha_bins['bin'], rotation='horizontal')

        plt.show()

    def analysis(self):
        self._data_filtering()
        self._create_alpha_return_df()
        self._plot()


class AlphaResearch(object):
    def __init__(self, raw_data, clean_data, alpha, analysis_cls):
        self.raw_data = raw_data
        self.clean_data = clean_data
        self.alpha = alpha
        self.analysis_cls = analysis_cls

    def data_cleansing(self):
        for f in self.raw_data.path:
            # Process raw data
            try:
                df = pd.read_csv(f, header=0)
                df.columns = self.raw_data.columns
                df = df.dropna()
                df = df.set_index(['symbol'])
                df.date = pd.to_datetime(df.date, format=self.raw_data.date_format)
                df.time = pd.to_datetime(df.time, format=self.raw_data.time_format).dt.time
            except ValueError:
                print 'Raw data cleansing error!'

            # Calculate returns using close or mid-price data
            for freq in [1, 2, 5, 10, 15]:
                df['return_'+str(freq)+self.alpha.horizon] = df.close.shift(-freq)/df.close - 1

            # Calculate alpha
            df[self.alpha.name] = (df.close - df['open']) / ((df.high - df.low) + .001)
            # df[self.alpha.name] = (-1) * df.close.rolling(window=5).corr(other=df.volume)

            # Save cleaned data
            self.clean_data.data = self.clean_data.data.append(df)

        self.clean_data.data.to_csv('cleaned_data/2016.csv', sep=',')
        print 'Data Cleansing Done.'

    def analysis(self):
        self.analysis_cls(self.clean_data, self.alpha).analysis()


if __name__ == "__main__":

    my_raw_data = Data(
        stamp='2016',
        path=glob.glob(os.path.join(os.getcwd(), 'raw_data/2016/*.csv')),
        columns=['symbol', 'date', 'time', 'open', 'high', 'low', 'close', 'volume'],
        date_format='%Y-%m-%d',
        time_format='%H:%M:%S'
    )
    my_clean_data = copy.deepcopy(my_raw_data)
    my_clean_data.path = glob.glob(os.path.join(os.getcwd(), 'cleaned_data/*.csv'))

    my_alpha = Alpha()

    research = AlphaResearch(my_raw_data, my_clean_data, my_alpha, BinAnalysis)
    research.data_cleansing()
    research.analysis()
