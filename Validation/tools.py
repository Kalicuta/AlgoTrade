import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display


def head_tail(df):
	display(df.head())
	display(df.tail())


def load_data(path, header=0, sep=','):
    return pd.concat((pd.read_csv(f, header=header, sep=sep) for f in path))


def drop_percentiles(df, column):
	return df[(df[column] > df[column].quantile(0.005)) & (df[column] < df[column].quantile(0.995))]
