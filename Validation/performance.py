import pandas as pd
from . import utils


def mean_return_by_quantile(factor_data,
                            by_date=False,
                            by_group=False,
                            demeaned=True):

    if demeaned:
        factor_data = utils.demean_forward_returns(factor_data)
    else:
        factor_data = factor_data.copy()

    grouper = ['factor_quantile']
    if by_date:
        grouper.append(factor_data.index.get_level_values('date'))

    if by_group:
        grouper.append('group')

    col = utils.get_forward_returns_columns(factor_data.columns)
    group_stats = factor_data.groupby(grouper)[col].agg(['mean', 'std', 'count'])

    mean_ret = group_stats.T.xs('mean', level=1).T

    return mean_ret


def factor_returns(factor_data, long_short=True, group_neutral=False):
    """
    Computes period wise returns for portfolio weighted by factor
    values. Weights are computed by demeaning factors and dividing
    by the sum of their absolute value (achieving gross leverage of 1).
    Parameters
    ----------
    factor_data : pd.DataFrame - MultiIndex
        A MultiIndex DataFrame indexed by date (level 0) and asset (level 1),
        containing the values for a single alpha factor, forward returns for each period,
        The factor quantile/bin that factor value belongs too, and (optionally) the group the
        asset belongs to.
    long_short : bool
        Should this computation happen on a long short portfolio?
        If yes, demean the alpha factors.
    group_neutral : bool
        If True, compute group neutral returns: each group will weight
        the same and returns demeaning will occur on the group level.
        And normalized.
    Returns
    -------
    returns : pd.DataFrame
        Period wise returns of dollar neutral portfolio weighted by factor value.
    """

    def to_weights(series, demean=False):
        if demean is True:
            demeaned_series = series - series.mean()
            return demeaned_series / demeaned_series.abs().sum()
        else:
            return series / series.abs().sum()

    # step 1: choose grouper
    grouper = [factor_data.index.get_level_values('date')]
    if group_neutral:
        grouper.append('group')

    # step 2: find weights
    weights = factor_data.groupby(grouper)['factor'].apply(to_weights, long_short)
    if group_neutral:
        weights = weights.groupby(level='date').apply(to_weights, False)

    # step 3: calculate returns
    weighted_returns = factor_data[utils.get_forward_returns_columns(factor_data.columns)].multiply(weights, axis=0)
    returns = weighted_returns.groupby(level='date').sum()

    return returns


def compute_mean_returns_spread(mean_returns, upper, lower):
    spread = mean_returns.xs(upper, level='factor_quantile') - mean_returns.xs(lower, level='factor_quantile')
    return spread
