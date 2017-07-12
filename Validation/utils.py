import pandas as pd
import numpy as np


def compute_forward_returns(prices, periods=(1, 5, 10), filter_zscore=None):
    forward_returns = pd.DataFrame(index=pd.MultiIndex.from_product(
        [prices.index, prices.columns], names=['date', 'asset'])
    )

    for period in periods:
        delta = prices.pct_change(period).shift(-period)

        if filter_zscore is not None:
            mask = abs(delta - delta.mean()) > (filter_zscore * delta.std())
            delta[mask] = np.nan

        forward_returns[period] = delta.stack()

    forward_returns.index = forward_returns.index.rename(['date', 'asset'])
    return forward_returns


def get_clean_factor_and_forward_returns(factor,
                                         forward_returns,
                                         by_group=False,
                                         groupby=None,
                                         groupby_labels=None,
                                         quantiles=20,
                                         bins=None,
                                         drop_zero=True):
    group_labels = None
    if by_group is True:
        group_labels = _grouping(factor, groupby=groupby, groupby_labels=groupby_labels)

    merged_data = _merging(factor, forward_returns, group_labels)
    merged_data['factor_quantile'] = _quantize_factor(merged_data,
                                                      quantiles=quantiles,
                                                      bins=bins,
                                                      by_group=by_group,
                                                      drop_zero=drop_zero)

    merged_data = merged_data.dropna()
    merged_data['factor_quantile'] = merged_data['factor_quantile'].astype(int)

    return merged_data


def _grouping(factor, groupby, groupby_labels):
    if isinstance(groupby, dict):
        diff = set(factor.index.get_level_values('asset')) - set(groupby.keys())
        if len(diff) > 0:
            raise KeyError("Assets {} not in group mapping".format(list(diff)))

        ss = pd.Series(groupby)
        groupby = pd.Series(index=factor.index, data=ss[factor.index.get_level_values('asset')].values)

    if groupby_labels is not None:
        diff = set(groupby.values) - set(groupby_labels.keys())
        if len(diff) > 0:
            raise KeyError("groups {} not in passed group names".format(list(diff)))

        sn = pd.Series(groupby_labels)
        groupby = pd.Series(index=factor.index, data=sn[groupby.values].values)

    return groupby.astype('category')


def _merging(factor, forward_returns, group_labels=None):

    merged_data = forward_returns.copy()
    factor = factor.copy()
    factor.index = factor.index.rename(['date', 'asset'])
    merged_data['factor'] = factor
    if group_labels is not None:
        merged_data['group'] = group_labels

    return merged_data.dropna()


def _quantize_factor(factor_data, quantiles=5, bins=None, by_group=False, drop_zero=True):

    def quantile_calc(x, _quantiles, _bins):
        if _quantiles is not None:
            return pd.qcut(x.rank(method='first'), _quantiles, labels=False) + 1
        elif _bins is not None:
            return pd.cut(x, _bins, labels=False) + 1
        raise ValueError('quantiles or bins should be provided')

    if drop_zero is True:
        factor_data = factor_data[factor_data['factor'] != 0.]

    grouper = [factor_data.index.get_level_values('date')]
    if by_group:
        grouper.append('group')

    factor_quantile = factor_data.groupby(grouper)['factor'].apply(quantile_calc, quantiles, bins)
    factor_quantile.name = 'factor_quantile'

    return factor_quantile.dropna()


def demean_forward_returns(factor_data, grouper=None):

    factor_data = factor_data.copy()

    if not grouper:
        grouper = factor_data.index.get_level_values('date')

    cols = get_forward_returns_columns(factor_data.columns)
    factor_data[cols] = factor_data.groupby(grouper)[cols].transform(lambda x: x - x.mean())

    return factor_data


def get_forward_returns_columns(columns):
    return columns[columns.astype('str').str.isdigit()]
