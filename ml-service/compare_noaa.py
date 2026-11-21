from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.preprocessing import StandardScaler

from data_loader import get_json
from flare_features import FEATURES, build_features, class_flux, daily_series
from flare_live import swpc_events

HERE = Path(__file__).resolve().parent


def read_ncei(paths):
    fl = pd.concat([pd.read_csv(p, usecols=["time", "flare_class"]) for p in paths], ignore_index=True)
    fl["time"] = pd.to_datetime(fl["time"], utc=True).dt.tz_localize(None)
    cls = fl["flare_class"].astype(str)
    return pd.DataFrame({"day": fl["time"].dt.normalize(), "cls": cls.str[0], "flux": cls.map(class_flux)})


mission = max((HERE / "data").glob("sci_xrsf-l2-flrpt_geo_s1995*.csv"))
old = read_ncei([mission])
m, c, peak = daily_series(old, pd.date_range("1996-01-01", "2019-12-31", freq="D"))
y = (m.shift(-1) > 0).astype(float)
y.iloc[-1] = np.nan
train = build_features(m, c, peak).assign(y=y).dropna()
scaler = StandardScaler().fit(train[FEATURES])
clf = LogisticRegression(max_iter=3000).fit(scaler.transform(train[FEATURES]), train["y"])

live = read_ncei(sorted((HERE / "data" / "live").glob("sci_xrsf-l2-flrpt_geo_y*.csv")))
swpc = swpc_events()
swpc["day"] = pd.to_datetime(swpc["day"])
cut = live["day"].max()
events = pd.concat([live[live["day"] < cut], swpc[swpc["day"] >= cut]], ignore_index=True)
yday = pd.Timestamp.now("UTC").tz_localize(None).normalize() - pd.Timedelta(days=1)
m2, c2, peak2 = daily_series(events, pd.date_range(pd.Timestamp(yday.year, 1, 1), yday, freq="D"))
X = build_features(m2, c2, peak2)

rows = get_json("https://services.swpc.noaa.gov/json/solar_probabilities.json", retries=3, timeout=30)
noaa = {pd.Timestamp(r["date"][:10]): (r["m_class_1_day"] / 100, r["x_class_1_day"] / 100) for r in rows}

base = train["y"].mean()
out = []
for day, (pm, px) in sorted(noaa.items()):
    prev = day - pd.Timedelta(days=1)
    if day > yday or prev not in X.index or X.loc[prev].isna().any():
        continue
    p = clf.predict_proba(scaler.transform(X.loc[[prev], FEATURES]))[0, 1]
    out.append({"доба": day.date(), "факт": int(m2.loc[day]), "наша": round(p, 3), "NOAA M": pm,
                "NOAA M+X": round(1 - (1 - pm) * (1 - px), 3),
                "частота 27 діб": round(float(X.loc[prev, "m_27d"]), 3), "кліматологія": round(base, 3)})
df = pd.DataFrame(out)
print(df.to_string(index=False))
print(f"\nДіб: {len(df)}, частка діб з M+: {df['факт'].mean():.2f}")
for col in ["наша", "NOAA M", "NOAA M+X", "частота 27 діб", "кліматологія"]:
    print(f"Brier {col:15s} {brier_score_loss(df['факт'], df[col]):.4f}")

df.to_csv(HERE.parent / "docs" / "flare_vs_noaa_30d.csv", index=False)