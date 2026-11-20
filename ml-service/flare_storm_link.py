import time
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import load_kp_gfz

DATA = Path(__file__).resolve().parent / "data"
FLARES = next(DATA.glob("sci_xrsf-l2-flrpt_geo_s1995*.csv"))
CLASSES = ["M", "X"]
STORM = 5.0
WINDOWS = {"−48…−24 год (до спалаху)": -16, "−24…0 год (до спалаху)": -8,
           "0-24 год": 1, "24-48 год": 9, "48-72 год": 17, "72-96 год": 25}


def kp_year(year):
    f = DATA / f"kp_{year}.csv"
    if f.exists():
        s = pd.read_csv(f, index_col=0)["kp"]
        s.index = pd.to_datetime(s.index, utc=True)
        return s
    s = load_kp_gfz(f"{year}-01-01T00:00:00Z", f"{year}-12-31T23:59:59Z")
    s.to_csv(f, header=True)
    time.sleep(1)
    return s


def forward_max(kp, start, n=8):
    return kp.rolling(n, min_periods=n).max().shift(-(start + n - 1))


kp = pd.concat([kp_year(y) for y in range(2000, 2026)]).sort_index()
kp_years = pd.Series(kp.index.year, index=kp.index)

fl = pd.read_csv(FLARES, usecols=["time", "flare_class"])
fl["time"] = pd.to_datetime(fl["time"], utc=True)
fl = fl[fl["flare_class"].str[0].isin(CLASSES)]
fl = fl[(fl["time"] >= pd.Timestamp("2000-01-01", tz="UTC")) & (fl["time"] < pd.Timestamp("2025-12-01", tz="UTC"))]

pos = kp.index.searchsorted(pd.DatetimeIndex(fl["time"]), side="right") - 1
ok = (pos >= 0) & (pos < len(kp) - 1)
fl, pos = fl[ok].copy(), pos[ok]
fl["year"] = fl["time"].dt.year
print(f"Спалахів класів {CLASSES} у вибірці: {len(fl)}")

rows = []
for label, start in WINDOWS.items():
    fm = forward_max(kp, start)
    valid = fm.notna()
    storm = fm >= STORM
    base_by_year = storm[valid].groupby(kp_years[valid]).mean()
    v = valid.iloc[pos].values
    observed = storm.iloc[pos].values[v]
    expected = base_by_year.reindex(fl["year"].values[v]).values
    rows.append({
        "вікно після піку": label,
        "спалахів": int(v.sum()),
        "P(буря) після спалаху": round(float(observed.mean()), 3),
        "P(буря) база того ж року": round(float(np.nanmean(expected)), 3),
        "відношення": round(float(observed.mean() / np.nanmean(expected)), 2),
    })
print(pd.DataFrame(rows).to_string(index=False))