import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob

plt.style.use('ggplot')

def data_cleansing(allFiles):
    """
    从raw data中挑选需要的信息（symbol, date, time, etc.）
    用price计算returns; 这里用了close price
    计算alpha
    将清理好的数据保存
    """
    
    i = 1
    cleaned_data = pd.DataFrame(columns=['symbol', 'date', 'time', 'open', 'high', 
                                         'low', 'close', 'volume', 'return'])
    temp_list = []
    
    for file_ in allFiles:
        
        df = pd.read_csv(file_, header=0)
        df.columns = ["symbol", "date", "time", "open", "high", "low", "close", "volume"]
        
        df = df.dropna()
        df = df.set_index(['symbol'])
        df.date = pd.to_datetime(df.date, format='%Y-%m-%d')
        df.time = pd.to_datetime(df.time, format='%H:%M:%S').dt.time
        date = df.head(1)['date'][0].date()

        df['return'] = df.close.shift(-1)/df.close - 1
#         df['return_2day'] = df.close.shift(-2)/df.close - 1
#         df['return_5day'] = df.close.shift(-5)/df.close - 1
#         df['return_10day'] = df.close.shift(-10)/df.close - 1
        
        df[alpha_name] = (df.close - df['open']) / ((df.high - df.low) + .001)
        temp_list.append(df)

    cleaned_data = pd.concat(temp_list)
    cleaned_data.to_csv('cleaned_data/' + '%s.csv'%year, sep=',') 


def data_processing(allFiles):
    full_data = pd.DataFrame()
    temp_list = []

    for _file in allFiles:
        df = pd.read_csv(_file, header=0, sep=',')
        print df.head()
#         df = df[(df['time'] <= '15:00') & (df[alpha_name] != 0)]
        df = df[df[alpha_name] != 0]
        temp_list.append(df)
    full_data = pd.concat(temp_list)
    full_data = full_data.dropna()
    full_data = full_data.sort_values(alpha_name)
    print full_data.tail()
    return full_data


def construct_alpha_bins(full_data, num_of_bin):
    list_of_df = np.array_split(full_data, num_of_bin)
    alpha_bins = pd.DataFrame(columns=[alpha_name, 'return'])
    
    # change alpha names (if only one alpha is studied, modify accordingly)
    for df in list_of_df:
        t = {'Alpha':[df[alpha_name].mean()],
             'return': [df['return_1day'].mean()*10000]}
        t = pd.DataFrame(t)
        alpha_bins = alpha_bins.append(t[['Alpha', 'return']])

    alpha_bins['bin'] = [i for i in xrange(1, 21, 1)]
    return alpha_bins


def plot(alpha_bins):
    fig, ax1 = plt.subplots(figsize=(10,6))
    ax2 = ax1.twinx()

    a = alpha_bins[['return', alpha_name]]
    a = a.reset_index(drop=True)
    a['return'].plot(kind='bar', ax=ax1)
    ax2.plot(a[alpha_name], marker='o', ls='-', color='b')
    # a[alpha_type].plot(ax=ax2, marker='o', ls='-', secondary_y=alpha_type, color='b')
    ax1.set_ylim((-15, 20))
    ax1.set_xlim((-1, 20))
    ax1.set_title(alpha_name+' - '+'1 day')
    ax2.set_ylim((-1, 1))

    ax1.set_ylabel('Avg. return (bps)')
    ax2.set_ylabel('Avg. alpha')

    ax1.set_xticklabels(alpha_bins['bin'], rotation='horizontal')
    ax1.set_xlabel('bin #')
    ax1.legend(loc=2)
    ax2.legend(loc=4)

    # ax2.set_yticks(np.linspace(ax2.get_yticks()[0], ax2.get_yticks()[-1],len(ax1.get_yticks())))

    plt.show()


if __name__ == "__main__":
#     freq = 1
    year = 2016
    alpha_name = 'Alpha'
    num_of_bin = 20

    path = os.getcwd()
    path_1 = glob.glob(os.path.join(path, "raw_data/%s/*.csv" %year))
    path_2 = glob.glob(os.path.join(path, "cleaned_data/%s.csv" %year))
    
    data_cleansing(path_1)
    full_data = data_processing(path_2)
    alpha_bins = construct_alpha_bins(full_data, num_of_bin)
    plot(alpha_bins)
