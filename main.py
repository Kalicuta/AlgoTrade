from algotrade.stratanalyzer import analyzer


sinewave = 'trade_list.csv'
a = analyzer.GeneralAnalyzer(sinewave)
a.start()

b = analyzer.HoldingAnalyzer()
b.start()
