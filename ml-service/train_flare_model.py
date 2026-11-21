import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.preprocessing import StandardScaler

from flare_features import FEATURES, build_features, class_flux, daily_series

HERE = Path(__file__).resolve().parent
FLARES = next((HERE / "data").glob("sci_xrsf-l2-flrpt_geo_s1995*.csv"))
fl = pd.read_csv(FLARES, usecols=["time", "flare_class"])
fl["time"] = pd.to_datetime(fl["time"], utc=True).dt.tz_localize(None)
cls_text = fl["flare_class"].astype(str)
events = pd.DataFrame({"day": fl["time"].dt.normalize(), "cls": cls_text.str[0],
                       "flux": cls_text.map(class_flux)})

days = pd.date_range("1996-01-01", events["day"].max(), freq="D")
m, c, peak = daily_series(events, days)
X = build_features(m, c, peak)
y = (m.shift(-1) > 0).astype(float)
y.iloc[-1] = np.nan
data = X.assign(y=y).dropna()


def fit(frame):
    scaler = StandardScaler().fit(frame[FEATURES])
    clf = LogisticRegression(max_iter=3000).fit(scaler.transform(frame[FEATURES]), frame["y"])
    return scaler, clf


train, test = data[:"2019-12-31"], data["2020-01-01":]
scaler, clf = fit(train)
p = clf.predict_proba(scaler.transform(test[FEATURES]))[:, 1]
bs = brier_score_loss(test["y"], p)
bs_clim = brier_score_loss(test["y"], np.full(len(test), train["y"].mean()))
print(f"Перевірка (навчання до 2019, тест {test.index.min():%Y-%m-%d} - {test.index.max():%Y-%m-%d}):")
print(f"  Brier {bs:.4f}, BSS {1 - bs / bs_clim:.3f}, ROC AUC {roc_auc_score(test['y'], p):.3f}")

scaler, clf = fit(data)
model = {"features": FEATURES, "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
         "coef": clf.coef_[0].tolist(), "intercept": float(clf.intercept_[0]),
         "trained_from": str(data.index.min().date()), "trained_until": str(data.index.max().date()),
         "n_days": int(len(data)), "base_rate": float(data["y"].mean())}
(HERE / "models").mkdir(exist_ok=True)
(HERE / "models" / "flare_logreg.json").write_text(json.dumps(model, indent=2), encoding="utf-8")
print("Збережено models/flare_logreg.json; коефіцієнти (стандартизовані ознаки):")
for name, w in zip(FEATURES, model["coef"]):
    print(f"  {name:8s} {w:+.3f}")