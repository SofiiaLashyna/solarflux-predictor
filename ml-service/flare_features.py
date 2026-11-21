import numpy as np
import pandas as pd

FLUX = {"A": 1e-8, "B": 1e-7, "C": 1e-6, "M": 1e-5, "X": 1e-4}
FEATURES = ["m_1d", "m_3d", "m_27d", "c_1d", "c_27d", "peak_1d", "m_27ago"]


def class_flux(s):
    try:
        return FLUX[s[:1]] * float(s[1:])
    except (KeyError, ValueError):
        return np.nan


def daily_series(events, days):
    m = (events[events["cls"].isin(["M", "X"])].groupby("day").size().reindex(days, fill_value=0) > 0).astype(int)
    c = (events[events["cls"].isin(["C", "M", "X"])].groupby("day").size().reindex(days, fill_value=0) > 0).astype(int)
    peak = np.log10(events.groupby("day")["flux"].max().reindex(days).clip(lower=1e-9)).fillna(-9)
    return m, c, peak


def build_features(m, c, peak):
    X = pd.DataFrame(index=m.index)
    X["m_1d"] = m
    X["m_3d"] = m.rolling(3).sum()
    X["m_27d"] = m.rolling(27).mean()
    X["c_1d"] = c
    X["c_27d"] = c.rolling(27).mean()
    X["peak_1d"] = peak
    X["m_27ago"] = m.shift(26)
    return X