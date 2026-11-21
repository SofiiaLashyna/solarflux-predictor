import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import get_json
from flare_features import build_features, class_flux, daily_series

HERE = Path(__file__).resolve().parent
MODEL = json.loads((HERE / "models" / "flare_logreg.json").read_text(encoding="utf-8"))
SWPC_7D = "https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json"
NOAA_PROBS = "https://services.swpc.noaa.gov/json/solar_probabilities.json"


def probability(features):
    x = np.array([features[f] for f in MODEL["features"]], dtype=float)
    z = (x - np.array(MODEL["mean"])) / np.array(MODEL["scale"])
    return float(1 / (1 + np.exp(-(MODEL["intercept"] + np.dot(z, MODEL["coef"])))))


def ncei_events(since):
    path = max((HERE / "data").glob("sci_xrsf-l2-flrpt_geo_s1995*.csv"))
    fl = pd.read_csv(path, usecols=["time", "flare_class"])
    fl["time"] = pd.to_datetime(fl["time"], utc=True).dt.tz_localize(None)
    fl = fl[fl["time"] >= since]
    cls = fl["flare_class"].astype(str)
    return pd.DataFrame({"day": fl["time"].dt.normalize(), "cls": cls.str[0], "flux": cls.map(class_flux)})


def swpc_events():
    rows = get_json(SWPC_7D, retries=3, timeout=60)
    out = []
    for f in (rows if isinstance(rows, list) else []):
        cls, t = str(f.get("max_class") or ""), f.get("max_time")
        if cls and t and not np.isnan(class_flux(cls)):
            out.append({"day": pd.to_datetime(t, utc=True).tz_localize(None).normalize(),
                        "cls": cls[:1], "flux": class_flux(cls)})
    return pd.DataFrame(out, columns=["day", "cls", "flux"])


def noaa_today():
    try:
        rows = get_json(NOAA_PROBS, retries=3, timeout=30)
        latest = max(rows, key=lambda r: r["date"])
        return {"date": latest["date"][:10], "m_class_1_day": latest["m_class_1_day"],
                "x_class_1_day": latest["x_class_1_day"]}
    except Exception as e:
        return {"error": str(e)}


def predict_today(now=None):
    now = now or datetime.now(timezone.utc)
    today = pd.Timestamp(now.year, now.month, now.day)
    last_day = today - pd.Timedelta(days=1)
    start = last_day - pd.Timedelta(days=45)

    swpc = swpc_events()
    if swpc.empty:
        raise RuntimeError("SWPC не повернув жодного спалаху")
    swpc["day"] = pd.to_datetime(swpc["day"])
    ncei = ncei_events(start)
    if ncei.empty:
        raise RuntimeError("У файлі NCEI немає свіжих спалахів: оновіть файл")
    cut = ncei["day"].max()                     
    first_full = swpc["day"].min() + pd.Timedelta(days=1)
    if first_full > cut:
        raise RuntimeError(f"Розрив між NCEI (до {cut:%Y-%m-%d}) і SWPC (з {first_full:%Y-%m-%d}): оновіть файл NCEI")
    events = pd.concat([ncei[ncei["day"] < cut], swpc[swpc["day"] >= cut]], ignore_index=True)
    events = events[events["day"] <= last_day]

    days = pd.date_range(start, last_day, freq="D")
    m, c, peak = daily_series(events, days)
    feats = build_features(m, c, peak).iloc[-1]
    return {"target_day": today.strftime("%Y-%m-%d"),
            "probability": round(probability(feats), 4),
            "features": {k: float(v) for k, v in feats.items()},
            "flares_in_window": len(events),
            "sources": {"ncei_before": str(cut.date()), "swpc_from": str(cut.date())},
            "model": "logistic-regression, flare-history features",
            "trained_until": MODEL["trained_until"],
            "noaa": noaa_today()}