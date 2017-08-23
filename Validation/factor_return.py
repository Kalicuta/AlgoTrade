def get_weighted_factor_data(factor_data_, long_short=True, group_neutral=False, equal_weighted=True):

    factor_data = factor_data_.copy()

    def to_factor_weighted_weights(group, is_long_short):
        if is_long_short:
            demeaned_series = group - group.mean()
            return (demeaned_series / demeaned_series.abs().sum()).abs()
        else:
            return (group / group.abs().sum()).abs()

    def to_equal_weighted_weights(group, is_long_short):
        group = group / group
        return (group / group.count()).abs()

    grouper = [factor_data.index.get_level_values('date')]

    # if group_neutral:
    #     grouper.append('group')

    if equal_weighted:
        weights = factor_data.groupby(grouper)['factor'].apply(to_equal_weighted_weights, long_short)
    else:
        weights = factor_data.groupby(grouper)['factor'].apply(to_factor_weighted_weights, long_short)

    # if group_neutral:
    #     weights = weights.groupby(level='date').apply(to_weights, False)

    columns = utils.get_forward_returns_columns(factor_data.columns)
    factor_data[columns] = factor_data[columns].multiply(weights, axis=0)
    
    return factor_data


def factor_returns(factor_data, 
                   long_short=True, 
                   group_neutral=False, 
                   show_sum_only=False,
                   period=1,
                   long_bin=1, 
                   short_bin=20,
                   equal_weighted=True):
    
    factor_data = factor_data[factor_data['factor_quantile'].isin([long_bin,short_bin])].copy()

    weighted_factor_data = get_weighted_factor_data(factor_data, equal_weighted=equal_weighted)

    columns = utils.get_forward_returns_columns(weighted_factor_data.columns)
    mask = weighted_factor_data.factor_quantile == short_bin
    weighted_factor_data.loc[mask, columns] *= -1

    long_weighted_factor_data = weighted_factor_data[weighted_factor_data['factor_quantile'] == long_bin].copy()
    short_weighted_factor_data = weighted_factor_data[weighted_factor_data['factor_quantile'] == short_bin].copy()
    
    long_returns = long_weighted_factor_data[columns].groupby(level='date').sum()
    short_returns = short_weighted_factor_data[columns].groupby(level='date').sum()
    total_returns = weighted_factor_data[columns].groupby(level='date').sum()

    final_returns = pd.concat([total_returns[period], long_returns[period], short_returns[period]], axis=1)
    final_returns.columns = ['total return', 'long return', 'short return']
    
    if show_sum_only:
        return final_returns['total return']
    else:
        return final_returns 
