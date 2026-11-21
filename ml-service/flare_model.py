from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"
FLARES = next(DATA.glob("sci_xrsf-l2-flrpt_geo_s1995*.csv"))
SILSO = DATA / "SN_d_tot_V2.0.csv"
TRAIN_END, TEST_START = "2019-12-31", "2020-01-01"

cols = ["year", "month", "day", "decimal_year", "ssn", "ssn_std", "n_obs", "provisional"]
sn = pd.read_csv(SILSO, sep=";", names=cols)
sn["date"] = pd.to_datetime(sn[["year", "month", "day"]])
ssn_raw = sn[sn["ssn"] >= 0].set_index("date")["ssn"].asfreq("D").interpolate(limit=3)

fl = pd.read_csv(FLARES, usecols=["time", "flare_class", "xrsb_irrad"])
fl["time"] = pd.to_datetime(fl["time"], utc=True).dt.tz_localize(None)
fl["day"] = fl["time"].dt.normalize()
fl["cls"] = fl["flare_class"].astype(str).str[0]

days = pd.date_range("1996-01-01", fl["day"].max(), freq="D")
m = fl[fl["cls"].isin(["M", "X"])].groupby("day").size().reindex(days, fill_value=0)
c = fl[fl["cls"].isin(["C", "M", "X"])].groupby("day").size().reindex(days, fill_value=0)
peak = np.log10(fl.groupby("day")["xrsb_irrad"].max().reindex(days).clip(lower=1e-9)).fillna(-9)
ssn = ssn_raw.reindex(days)

X = pd.DataFrame(index=days)
X["m_1d"] = m
X["m_3d"] = m.rolling(3).sum()
X["m_27d"] = m.rolling(27).mean()
X["c_1d"] = c
X["c_27d"] = c.rolling(27).mean()
X["peak_1d"] = peak
X["ssn"] = ssn
X["ssn_27d"] = ssn.rolling(27).mean()
X["ssn_d3"] = ssn - ssn.shift(3)
X["m_27ago"] = m.shift(26)
y = (m.shift(-1) > 0).astype(float)
y[y.index[-1]] = np.nan

data = X.assign(y=y, rate27=(m > 0).rolling(27).mean()).dropna()
train, test = data[:TRAIN_END], data[TEST_START:]
FEATURES = list(X.columns)
print(f"Дні навчання: {len(train)}, частка діб з M+ спалахом {train['y'].mean():.3f}")
print(f"Дні тесту:    {len(test)}, частка діб з M+ спалахом {test['y'].mean():.3f}")
print("\nДоби з M+ спалахом по роках (перевірка узгодженості каталогу):")
print((m > 0).groupby(m.index.year).sum().to_string())


def tss(y_true, p, thr):
    pred = p >= thr
    tp = int((pred & (y_true == 1)).sum()); fn = int((~pred & (y_true == 1)).sum())
    fp = int((pred & (y_true == 0)).sum()); tn = int((~pred & (y_true == 0)).sum())
    return tp / max(tp + fn, 1) - fp / max(fp + tn, 1)


def best_threshold(y_true, p):
    return max(np.unique(np.round(p, 3)), key=lambda t: tss(y_true, p, t))


ytr, yte = train["y"].values, test["y"].values
base = ytr.mean()
cond = {1: train.loc[train["m_1d"] > 0, "y"].mean(), 0: train.loc[train["m_1d"] == 0, "y"].mean()}

preds = {
    "кліматологія": (np.full(len(train), base), np.full(len(test), base)),
    "за вчорашнім спалахом": (np.where(train["m_1d"] > 0, cond[1], cond[0]),
                              np.where(test["m_1d"] > 0, cond[1], cond[0])),
    "частота за 27 діб": (train["rate27"].values, test["rate27"].values),
}
models = {
    "логістична регресія": make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
    "градієнтний бустинг": HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300,
                                                          random_state=42),
}
for name, model in models.items():
    model.fit(train[FEATURES], ytr)
    preds[name] = (model.predict_proba(train[FEATURES])[:, 1], model.predict_proba(test[FEATURES])[:, 1])

bs_clim = brier_score_loss(yte, preds["кліматологія"][1])
rows = []
for name, (ptr, pte) in preds.items():
    thr = best_threshold(ytr, ptr)
    bs = brier_score_loss(yte, pte)
    rows.append({"метод": name, "Brier": round(bs, 4), "BSS": round(1 - bs / bs_clim, 3),
                 "ROC AUC": round(roc_auc_score(yte, pte), 3), "TSS": round(tss(yte, pte, thr), 3),
                 "поріг (навчання)": round(float(thr), 3)})
res = pd.DataFrame(rows)
print(f"\nТест {test.index.min():%Y-%m-%d} - {test.index.max():%Y-%m-%d}:")
print(res.to_string(index=False))

best = models["градієнтний бустинг"].predict_proba(test[FEATURES])[:, 1]
bins = pd.cut(best, [0, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8, 1.0], include_lowest=True)
calib = pd.DataFrame({"p": best, "y": yte}).groupby(bins, observed=True).agg(
    передбачено=("p", "mean"), фактично=("y", "mean"), діб=("y", "size"))
print("\nКалібрування градієнтного бустингу (тест):")
print(calib.round(3).to_string())

(ROOT / "docs").mkdir(exist_ok=True)
res.to_csv(ROOT / "docs" / "flare_model_results.csv", index=False)