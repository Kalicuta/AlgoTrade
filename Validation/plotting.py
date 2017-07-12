import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
plt.style.use('ggplot')

DECIMAL_TO_BPS = 10000


def plot_quantile_returns_bar(mean_return, ax=None):

    mean_return = mean_return.copy()

    if ax is None:
        f, ax = plt.subplots(1, 1, figsize=(12, 6))

    mean_return.multiply(DECIMAL_TO_BPS).plot(kind='bar', title="Mean Return By Factor Quantile", ax=ax)
    ax.set(xlabel='', ylabel='Mean Return (bps)')

    return ax


def plot_quantile_returns_bar_by_group(mean_return, ax=None):

    mean_return = mean_return.copy()

    num_group = len(mean_return.index.get_level_values('group').unique())

    if ax is None:
        v_spaces = (num_group + 1) // 2
        f, ax = plt.subplots(v_spaces, 2, sharex=False, sharey=True, figsize=(18, 6 * v_spaces))
        ax = ax.flatten()

    for a, (sc, cor) in zip(ax, mean_return.groupby(level='group')):
        cor.xs(sc, level='group').multiply(DECIMAL_TO_BPS).plot(kind='bar', title=sc, ax=a)
        a.set(xlabel='', ylabel='Mean Return (bps)')

    return ax


def plot_mean_quantile_returns_spread_time_series(mean_returns_spread):

    for column in mean_returns_spread:

        periods = mean_returns_spread[column].name

        f, ax = plt.subplots(figsize=(18, 6))

        mean_returns_spread_bps = mean_returns_spread[column].multiply(DECIMAL_TO_BPS)
        mean_returns_spread_bps.plot(alpha=0.7, ax=ax, lw=1, color='green')
        mean_returns_spread_bps.rolling(window=22, center=False).mean().plot(color='orange', alpha=1, lw=2, ax=ax)

        ax.legend(['mean returns spread', '1 month moving avg'], loc='upper right')
        title = ('Top Minus Bottom Quantile Mean Return ({} Period Forward Return)'.format(periods))
        ax.set(ylabel='Difference In Quantile Mean Return (bps)', xlabel='', title=title)
        ax.axhline(0.0, linestyle='-', color='black', lw=1, alpha=0.8)


def plot_cumulative_returns(factor_returns, period=1, ax=None):

    if ax is None:
        f, ax = plt.subplots(1, 1, figsize=(18, 6))

    factor_returns = factor_returns.copy()

    if period > 1:
        def compound_returns(ret, n):
            return (np.nanmean(ret) + 1)**(1./n) - 1
        factor_returns = pd.rolling_apply(factor_returns, period, compound_returns, min_periods=1, args=(period,))

    factor_returns.add(1).cumprod().plot(ax=ax, lw=3, color='forestgreen', alpha=0.6)
    ax.set(ylabel='Cumulative Returns',
           title='Factor Weighted Long/Short Portfolio Cumulative Return ({} Fwd Period)'.format(period), xlabel='')
    ax.axhline(1.0, linestyle='-', color='black', lw=1)

    return ax


def plot_cumulative_returns_by_quantile(quantile_returns, bin_list=None, period=1, ax=None):
    if ax is None:
        f, ax = plt.subplots(1, 1, figsize=(18, 6))

    return_wide = quantile_returns.reset_index().pivot(index='date', columns='factor_quantile', values=period)

    if period > 1:
        def compound_returns(ret, n):
            return (np.nanmean(ret) + 1)**(1./n) - 1
        return_wide = pd.rolling_apply(return_wide, period, compound_returns, min_periods=1, args=(period,))

    cum_ret = return_wide.add(1).cumprod()

    if bin_list is not None:
        cum_ret = cum_ret[bin_list]

    cum_ret.plot(lw=2, ax=ax)
    ax.legend()
    y_min, y_max = cum_ret.min().min(), cum_ret.max().max()

    ax.set(ylabel='Log Cumulative Returns',
           title='Cumulative Return by Quantile ({} Period Forward Return)'.format(period),
           xlabel='',
           yscale='symlog',
           yticks=np.linspace(y_min, y_max, 5),
           ylim=(y_min, y_max))

    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.axhline(1.0, linestyle='-', color='black', lw=1)

    return ax
