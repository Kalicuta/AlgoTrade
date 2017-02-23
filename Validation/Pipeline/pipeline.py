import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    def __init__(self, name='trial alpha', formula=None, horizon='day'):
        self.name = name
        self.formula = formula
        self.horizon = horizon


class Analysis(object):
    def __init__(self, data, alpha):
        self.research_data = data
        self.alpha = alpha

    def analysis(self):
        raise NotImplementedError


class DataClean(object):
    def __init__(self, raw_data, clean_data=None, alpha=None):
        self.raw_data = raw_data
        self.clean_data = clean_data
        self.alpha = alpha

    def data_cleansing(self):
        raise NotImplementedError


class AlphaValidation(Analysis):
    def __init__(self, data, alpha, bin_num=20):
        Analysis.__init__(self, data, alpha)
        self.num_of_bins = bin_num
        self.alpha_return = pd.DataFrame()

    def analysis(self):
        bin_dict = {i: pd.DataFrame() for i in xrange(1, self.num_of_bins+1, 1)}

        grouped = pd.groupby(self.research_data.data, by=[self.research_data.data.date])

        for time_stamp, group in grouped:
            # Filter the input data
            group = group[group[self.alpha.name] != 0]
            group = group.dropna()
            group = group.sort_values(self.alpha.name)

            # Partition daily data into n bins
            partitions = np.array_split(group, self.num_of_bins)
            for i in xrange(1, self.num_of_bins+1, 1):
                bin_dict[i] = bin_dict[i].append(partitions[i-1])

        # Alpha/Return analysis
        for i in xrange(1, self.num_of_bins+1, 1):
            alpha_bin = pd.DataFrame({
                'bin': [i],
                self.alpha.name: [bin_dict[i][self.alpha.name].mean()],
                'return': [bin_dict[i]['return'].mean()*10000]
            })
            self.alpha_return = self.alpha_return.append(alpha_bin[['bin', self.alpha.name, 'return']],
                                                         ignore_index=True)
        self.alpha_return = self.alpha_return.set_index('bin')

        self._plot()
        return self.alpha_return

    def _plot(self):
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        self.alpha_return['return'].plot(kind='bar', ax=ax1, alpha=0.8)
        ax2.plot(ax1.get_xticks(), self.alpha_return[self.alpha.name], marker='o', ls='-', color='b', alpha=0.5)

        ax1.set_title(self.alpha.name+' - '+self.alpha.horizon)
        ax1.set_ylabel('Ave. return (bps)')
        ax1.legend(loc=2)
        ax2.set_ylabel('Ave. alpha')
        ax2.legend(loc=4)

        plt.show()
