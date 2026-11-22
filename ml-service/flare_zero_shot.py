from pathlib import Path

import numpy as np
import pandas as pd
import torch
from chronos import BaseChronosPipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from flare_features import FEATURES, build_features, class_flux, daily_series

HERE = Path(__file__).resolve().parent
CTX, BATCH = 256, 128
LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
M_THRESHOLD = -5.0
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

mission = max((HERE / "data").glob("sci_xrsf-l2-flrpt_geo_s1995*.csv"))
fl = pd.read_csv(mission, usecols=["time", "flare_class"])
fl["time"] = pd.to_datetime(fl["time"], utc=True).dt.tz_localize(None)
cls = fl["flare_class"].astype(str)
events = pd.DataFrame({"day": fl["time"].dt.normalize(), "cls": cls.str[0], "flux": cls.map(class_flux)})

days = pd.date_range("1996-01-01", events["day"].max(), freq="D")
m, c, peak = daily_series(events, days)
X = build_features(m, c, peak)
y = (m.shift(-1) > 0).astype(float)
y.iloc[-1] = np.nan
data = X.assign(y=y).dropna()
train, test = data[:"2019-12-31"], data["2020-01-01":]
print(f"Тест: {test.index.min():%Y-%m-%d} - {test.index.max():%Y-%m-%d}, діб {len(test)}, "
      f"частка діб з M+: {test['y'].mean():.3f}; пристрій: {DEVICE}")

scaler = StandardScaler().fit(train[FEATURES])
clf = LogisticRegression(max_iter=3000).fit(scaler.transform(train[FEATURES]), train["y"])
preds = {
    "кліматологія": np.full(len(test), train["y"].mean()),
    "частота за 27 діб": test["m_27d"].values,
    "логістична регресія (наша)": clf.predict_proba(scaler.transform(test[FEATURES]))[:, 1],
}

pipe = BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map=DEVICE,
                                           torch_dtype=torch.float32)
pos = days.get_indexer(test.index)


def forecast_quantiles(values):
    out = []
    for i in range(0, len(pos), BATCH):
        contexts = [torch.tensor(values[p - CTX + 1: p + 1]) for p in pos[i:i + BATCH]]
        q, _ = pipe.predict_quantiles(contexts, prediction_length=1, quantile_levels=LEVELS)
        out.append(q[:, 0, :].cpu().numpy())
    return np.vstack(out)


q_bin = forecast_quantiles(m.values.astype(np.float32))
p_bin = np.clip(np.nan_to_num(q_bin).mean(axis=1), 0.0, 1.0)
q_flux = np.sort(np.nan_to_num(forecast_quantiles(peak.clip(lower=-8).values.astype(np.float32)),
                               nan=-8.0), axis=1)
p_flux = np.array([1 - np.interp(M_THRESHOLD, q, LEVELS, left=0.05, right=0.95) for q in q_flux])
print(f"Недійсних прогнозів у ряді 0/1: {int(np.isnan(q_bin).any(axis=1).sum())} з {len(q_bin)}")
preds["Chronos-Bolt, ряд 0/1"] = p_bin
preds["Chronos-Bolt, log10 піку потоку"] = p_flux

bs_clim = brier_score_loss(test["y"], preds["кліматологія"])
rows = []
for name, p in preds.items():
    bs = brier_score_loss(test["y"], p)
    rows.append({"метод": name, "Brier": round(bs, 4), "BSS": round(1 - bs / bs_clim, 3),
                 "ROC AUC": round(roc_auc_score(test["y"], p), 3)})
res = pd.DataFrame(rows)
print("\n" + res.to_string(index=False))
(HERE.parent / "docs").mkdir(exist_ok=True)
res.to_csv(HERE.parent / "docs" / "flare_zero_shot_results.csv", index=False)

# --- блоковий bootstrap по місяцях: чи значуща різниця Brier
sq = {k: (p - test["y"].values) ** 2 for k, p in preds.items()}
months = test.index.to_period("M")
groups = [np.where(months == mth)[0] for mth in months.unique()]
rng = np.random.default_rng(42)


def block_ci(a, b, n=5000):
    diffs = []
    for _ in range(n):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        diffs.append((sq[a][idx] - sq[b][idx]).mean())
    return (sq[a] - sq[b]).mean(), np.percentile(diffs, [2.5, 97.5])


print("\nΔ Brier = (перший метод) - (другий); плюс означає, що другий кращий")
for a, b in [("Chronos-Bolt, log10 піку потоку", "логістична регресія (наша)"),
             ("Chronos-Bolt, ряд 0/1", "Chronos-Bolt, log10 піку потоку")]:
    mean, ci = block_ci(a, b)
    print(f"{a} -> {b}: {mean:+.4f}, 95% ДІ [{ci[0]:+.4f}, {ci[1]:+.4f}]")