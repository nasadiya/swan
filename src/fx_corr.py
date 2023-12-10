import numpy as np
import pandas as pd
import yfinance as yf
import datetime as dt
from dateutil.relativedelta import relativedelta


def corr_data(pairs=['GBPEUR', 'JPYEUR'],
              start=dt.datetime.today() - relativedelta(years=10),
              end=dt.datetime.today(),
              rolling_corr=252):
    # get the data sets
    symbol_len = 3
    year_bdays = rolling_corr
    split_pairs = []
    individuals = []
    for pair in pairs:
        split = [pair[:symbol_len],pair[symbol_len:]]
        split_pairs.append(split)
        individuals += split
    # unique currencies to extract
    unique_codes = list(set(individuals))
    # extract the codes and merge into a dataframe
    for i,code in enumerate(unique_codes):
        if i == 0:
            placeholder = pd.DataFrame(yf.download(code + '=X',
                                                   start=start,
                                                   end=end,
                                                   progress=False).Close.rename(code))
        else:
            new = yf.download(code + '=X',
                              start=start,
                              end=end,
                              progress=False).Close.rename(code)
            placeholder = placeholder.merge(new, left_on='Date', right_on='Date')
    currs = placeholder.copy()
    placeholder = placeholder.pct_change().dropna()
    # create correlation series
    for i, pair in enumerate(pairs):
        split_pair = split_pairs[i]
        # compute correlation vector
        data = placeholder[split_pair].values
        holder = np.empty(data.shape[0])
        holder[:] = np.nan
        for i in range(year_bdays, data.shape[0]):
            corr = np.corrcoef(data[(i-year_bdays):i,0],data[(i-year_bdays):i,1])
            holder[i] = corr[0,1]
        placeholder = pd.concat([placeholder,pd.Series(data=holder,name=pair,index=placeholder.index)],axis=1)
    return currs, placeholder
