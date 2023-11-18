import warnings
import numpy as np
import pandas as pd
import QuantLib as ql
warnings.filterwarnings('ignore')


def make_instruments(r_6m=0.025,
                     r_1y=0.031,
                     r_2y=0.032,
                     r_3y=0.035,
                     r_4y=0.040):
    return [('depo', '6M', r_6m),  # 0.025
            ('swap', '1Y', r_1y),  # 0.031
            ('swap', '2Y', r_2y),  # 0.032
            ('swap', '3Y', r_3y),  # 0.035
            ('swap', '4Y', r_4y)]  # 0.040


def calculate_swap(instruments, tenor="3y", fixed_rate=0.0, fwd_strt="2D", nominal=1e6):
    yts = ql.RelinkableYieldTermStructureHandle()
    helpers = ql.RateHelperVector()
    index = ql.Euribor3M(yts)
    for instrument, tenor, rate in instruments:
        if instrument == 'depo':
            helpers.append( ql.DepositRateHelper(rate, index) )
        if instrument == 'fra':
            monthsToStart = ql.Period(tenor).length()
            helpers.append( ql.FraRateHelper(rate, monthsToStart, index) )
        if instrument == 'swap':
            swapIndex = ql.EuriborSwapIsdaFixA(ql.Period(tenor))
            helpers.append( ql.SwapRateHelper(rate, swapIndex))
    curve = ql.PiecewiseLogCubicDiscount(2, ql.TARGET(), helpers, ql.Actual365Fixed())
    yts.linkTo(curve)
    engine = ql.DiscountingSwapEngine(yts)
    tenor = ql.Period(tenor)
    fixedRate = fixed_rate
    forwardStart = ql.Period(fwd_strt)

    swap = ql.MakeVanillaSwap(tenor, index, fixedRate, forwardStart, Nominal=nominal, pricingEngine=engine)

    return swap
