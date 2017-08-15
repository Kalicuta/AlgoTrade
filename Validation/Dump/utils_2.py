import pandas as pd
import numpy as np
from scipy import stats as scistats


# def RunMultipleDayBackTest(dfBinedReturns, day, alpha_name, date_list_valid, isMomentum=False, bin_num=10, verbose=False):
#     dfBinedReturns['alphaRank'] = CalcDailyRank(dfBinedReturns, alpha_name=alpha_name)
#     try:
#         dfBinedReturns['Bin'] = CalcDailyBin(dfBinedReturns, alpha_name=alpha_name, bin_num=bin_num)        
#     except Exception as e:
#         print 'RunMultipleDayBackTest: Cannot use alpha value to fully cut Bin, fall back to use rank'
#         dfBinedReturns['Bin'] = CalcDailyBin(dfBinedReturns, alpha_name='alphaRank', bin_num=bin_num)                
#     if isMomentum:
#         dfBinedReturns['Side'] = np.where(dfBinedReturns['Bin']==1, -1, np.where(dfBinedReturns['Bin']==bin_num, 1, 0))
#     else:
#         dfBinedReturns['Side'] = np.where(dfBinedReturns['Bin']==1, 1, np.where(dfBinedReturns['Bin']==bin_num, -1, 0))
#     RunBackTest(dfBinedReturns, day, alpha_name, date_list_valid, verbose)


def add_size_info_to_factor_data(factor_data, is_momentum=False, bin_num=10):
	if is_momentum:
		factor_data['side'] = np.where(factor_data['factor_quantile']==1, -1, np.where(factor_data['factor_quantile']==bin_num, 1, 0))
	else:
		factor_data['side'] = np.where(factor_data['factor_quantile']==1, 1, np.where(factor_data['factor_quantile']==bin_num, -1, 0))
	return factor_data




def calculate_final_return(factor_data):  #  CalcFinalReturn(dfReturns, dateList, fee=None):
	date_list = [factor_data.index.get_level_values('date').unique()]
	final_return = pd.DataFrame(index=date_list)
	factor_data = factor_data.reset_index()
	final_return['Return'] = factor_data.groupby('date').apply(lambda df: df[1].sum())
	final_return['LongReturn'] = factor_data.groupby('date').apply(lambda df: df[df['side']>0][1].sum())
	final_return['ShortReturn'] = factor_data.groupby('date').apply(lambda df: df[df['side']<0][1].sum())

	final_return['LongCnt'] = factor_data.groupby('date').apply(lambda df: (df[df['side']>0]['side']).sum())
	final_return['ShortCnt'] = factor_data.groupby('date').apply(lambda df: (df[df['side']<0]['side']).sum())
	final_return['BookSize'] = abs(final_return['LongCnt']) + abs(final_return['ShortCnt'])

	final_return['CumReturn'] = final_return['Return'].cumsum()
	final_return['CumLongReturn'] = final_return['LongReturn'].cumsum()
	final_return['CumShortReturn'] = final_return['ShortReturn'].cumsum()

	# Calculate max drawdown
	max2here = final_return['CumReturn'].expanding(min_periods=1).max()
	final_return['DrawDown']=final_return['CumReturn']-max2here        
	max2here = final_return['CumLongReturn'].expanding(min_periods=1).max()
	final_return['LongDrawDown']=final_return['CumLongReturn']-max2here   

	return final_return


def calculate_sharpe_ratio(returns, N=252, verbose = False):
    vol = returns.std()
    sim_mean = returns.mean()
    # geo_mean = scistats.gmean(returns + 1) - 1
    simple_sharpe = np.sqrt(N) * sim_mean / vol
    # geo_sharpe = np.sqrt(N) * geo_mean / vol
    vol *= np.sqrt(N)
    if verbose: 
        print "Simple: %f\t| " % (simple_sharpe),
        # print "Geo.: %f\t|" % (geo_sharpe),
        print "Vol.: %f" % (vol)
    return (simple_sharpe, sim_mean * N, vol)
    # return (simple_sharpe, geo_sharpe, sim_mean * N, geo_mean * N, vol)


def calculate_return_metrics(final_return, sharpe_only=False):
	book_size = final_return['BookSize']

	if sharpe_only:
		sharpe_return = final_return[book_size != 0].copy()
		sharpe = calculate_sharpe_ratio(sharpe_return['Return'])
		print sharpe
		return sharpe[0]

	# Only trade days
	average_book_size = book_size[book_size != 0].mean()
	print 'Trading Days: %d/%d' % (len(book_size[book_size != 0]), len(book_size))
	sharpe_return = final_return[book_size != 0].copy()
	sharpe = calculate_sharpe_ratio(sharpe_return['Return'])
	dfMetrics = pd.DataFrame(list(sharpe)).T
	dfMetrics.columns = ['Sharpe', 'Ann. PnL', 'Ann. Vol']
	dfMetrics.index = ['Long/Short']
	dfMetrics['AvgBookSize'] = average_book_size
	dfMetrics['Ann. Return'] = dfMetrics['Ann. PnL'][0] / average_book_size    

	dfMetrics['MDD'] = final_return['DrawDown'].min()
	dfMetrics['MDD%'] = final_return['DrawDown'].min() / average_book_size    
	dfMetrics['PnL'] = final_return.iloc[-1]['CumReturn']
	# dfMetrics['Turnover'] = final_return['Turnover'].mean()
	dfMetrics=dfMetrics[['Sharpe', 'PnL', 'AvgBookSize', 'MDD', 'Ann. Return', 'MDD%']]    
	dfAllMetrics = dfMetrics.copy()		

	return dfAllMetrics


############################

'''
Quantopian/empyrical/empyrical/stats.py
'''

def cum_returns(returns, starting_value=0):
	"""
	Compute cumulative returns from simple returns.
	Parameters
	----------
	returns : pd.Series, np.ndarray, or pd.DataFrame
	    Returns of the strategy as a percentage, noncumulative.
	     - Time series with decimal returns.
	     - Example:
	        2015-07-16    -0.012143
	        2015-07-17    0.045350
	        2015-07-20    0.030957
	        2015-07-21    0.004902.
	    - Also accepts two dimensional data. In this case,
	        each column is cumulated.
	starting_value : float, optional
	   The starting returns.
	Returns
	-------
	pd.Series, np.ndarray, or pd.DataFrame
	    Series of cumulative returns.
	Notes
	-----
	For increased numerical accuracy, convert input to log returns
	where it is possible to sum instead of multiplying.
	PI((1+r_i)) - 1 = exp(ln(PI(1+r_i)))     # x = exp(ln(x))
	                = exp(SIGMA(ln(1+r_i))   # ln(a*b) = ln(a) + ln(b)
	"""
	# df_price.pct_change() adds a nan in first position, we can use
	# that to have cum_logarithmic_returns start at the origin so that
	# df_cum.iloc[0] == starting_value
	# Note that we can't add that ourselves as we don't know which dt
	# to use.

	if len(returns) < 1:
		return type(returns)([])

	if np.any(np.isnan(returns)):
		returns = returns.copy()
		returns[np.isnan(returns)] = 0.

	df_cum = (returns/82 + 1).cumprod(axis=0)

	if starting_value == 0:
		return df_cum - 1
	else:
		return df_cum * starting_value


def cum_returns_final(returns, starting_value=0):
	"""
	Compute total returns from simple returns.
	Parameters
	----------
	returns : pd.Series or np.ndarray
	    Returns of the strategy as a percentage, noncumulative.
	     - Time series with decimal returns.
	     - Example:
	        2015-07-16    -0.012143
	        2015-07-17    0.045350
	        2015-07-20    0.030957
	        2015-07-21    0.004902.
	starting_value : float, optional
	   The starting returns.
	Returns
	-------
	float
	"""

	if len(returns) == 0:
		return np.nan

	return cum_returns(np.asanyarray(returns), starting_value=starting_value)[-1]


def max_drawdown(returns):
	"""
	Determines the maximum drawdown of a strategy.
	Parameters
	----------
	returns : pd.Series or np.ndarray
	    Daily returns of the strategy, noncumulative.
	    - See full explanation in :func:`~empyrical.stats.cum_returns`.
	Returns
	-------
	float
	    Maximum drawdown.
	Note
	-----
	See https://en.wikipedia.org/wiki/Drawdown_(economics) for more details.
	"""

	if len(returns) < 1:
		return np.nan

	if type(returns) == pd.Series:
		returns = returns.values

	cumulative = np.insert(cum_returns(returns, starting_value=100), 0, 100)
	max_return = np.fmax.accumulate(cumulative)

	return np.nanmin((cumulative - max_return) / max_return)


def sharpe_ratio(returns):#, risk_free=0, period=DAILY, annualization=None):
    # """
    # Determines the Sharpe ratio of a strategy.
    # Parameters
    # ----------
    # returns : pd.Series or np.ndarray
    #     Daily returns of the strategy, noncumulative.
    #     - See full explanation in :func:`~empyrical.stats.cum_returns`.
    # risk_free : int, float
    #     Constant risk-free return throughout the period.
    # period : str, optional
    #     Defines the periodicity of the 'returns' data for purposes of
    #     annualizing. Value ignored if `annualization` parameter is specified.
    #     Defaults are:
    #         'monthly':12
    #         'weekly': 52
    #         'daily': 252
    # annualization : int, optional
    #     Used to suppress default values available in `period` to convert
    #     returns into annual returns. Value should be the annual frequency of
    #     `returns`.
    # Returns
    # -------
    # float
    #     Sharpe ratio.
    #     np.nan
    #         If insufficient length of returns or if if adjusted returns are 0.
    # Note
    # -----
    # See https://en.wikipedia.org/wiki/Sharpe_ratio for more details.
    # """
	if len(returns) < 2:
		return np.nan

	# ann_factor = annualization_factor(period, annualization)
	ann_factor = 252

	# returns_risk_adj = np.asanyarray(_adjust_returns(returns, risk_free))
	returns_risk_adj = returns
	returns_risk_adj = returns_risk_adj[~np.isnan(returns_risk_adj)]

	if np.std(returns_risk_adj, ddof=1) == 0:
		return np.nan

	return np.mean(returns_risk_adj) / np.std(returns_risk_adj, ddof=1) * np.sqrt(ann_factor)



'''
Quantopian/pyfolio/pyfolio/ 
'''

SIMPLE_STAT_FUNCS = [
	# empyrical.annual_return,
	cum_returns_final,
	# empyrical.annual_volatility,
	sharpe_ratio
	# empyrical.max_drawdown
]

STAT_FUNC_NAMES = {
	# 'annual_return': 'Annual return',
	'cum_returns_final': 'Cumulative returns',
	# 'annual_volatility': 'Annual volatility',
	'sharpe_ratio': 'Sharpe ratio'
	# 'max_drawdown': 'Max drawdown'
}


def perf_stats(returns, factor_returns=None, positions=None, transactions=None):
	"""
	Calculates various performance metrics of a strategy, for use in
	plotting.show_perf_stats.
	Parameters
	----------
	returns : pd.Series
	    Daily returns of the strategy, noncumulative.
	     - See full explanation in tears.create_full_tear_sheet.
	factor_returns : pd.Series (optional)
	    Daily noncumulative returns of the benchmark.
	     - This is in the same style as returns.
	    If None, do not compute alpha, beta, and information ratio.
	positions : pd.DataFrame
	    Daily net position values.
	     - See full explanation in tears.create_full_tear_sheet.
	transactions : pd.DataFrame
	    Prices and amounts of executed trades. One row per trade.
	    - See full explanation in tears.create_full_tear_sheet
	Returns
	-------
	pd.Series
	    Performance metrics.
	"""
	stats = pd.Series()
	for stat_func in SIMPLE_STAT_FUNCS:
		stats[STAT_FUNC_NAMES[stat_func.__name__]] = stat_func(returns)

	# if positions is not None:
	#     stats['Gross leverage'] = gross_lev(positions).mean()
	#     if transactions is not None:
	#         stats['Daily turnover'] = get_turnover(positions,
	#                                                transactions).mean()
	# if factor_returns is not None:
	#     for stat_func in FACTOR_STAT_FUNCS:
	#         res = stat_func(returns, factor_returns)
	#         stats[STAT_FUNC_NAMES[stat_func.__name__]] = res

	return stats



def show_perf_stats(returns, factor_returns, positions=None, transactions=None):
	perf_func = perf_stats

	perf_stats_all = perf_func(returns, factor_returns=factor_returns, positions=positions, transactions=transactions)

	# print('Backtest months: ' + str(int(len(returns) / APPROX_BDAYS_PER_MONTH)))
	perf_stats = pd.DataFrame(perf_stats_all, columns=['Backtest'])

	# for column in perf_stats.columns:
	#     for stat, value in perf_stats[column].iteritems():
	#         if stat in STAT_FUNCS_PCT:
	#             perf_stats.loc[stat, column] = str(np.round(value * 100, 1)) + '%'

	# utils.print_table(perf_stats, fmt='{0:.2f}')
	display(perf_stats)


