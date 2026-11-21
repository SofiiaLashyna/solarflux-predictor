import json
import time
from pathlib import Path

import pandas as pd

from cme_models import const_speed_hours, dbm_hours
from data_loader import get_json

ROOT = Path(__file__).resolve().parent.parent
CACHE = Path(__file__).resolve().parent / "data" / "donki"
CACHE.mkdir(parents=True, exist_ok=True)
DONKI = "https://ccmc.gsfc.nasa.gov/DONKI-API/get"


def reduce_cme(c):
    analyses = c.get("cmeAnalyses") or []
    best = next((a for a in analyses if a.get("isMostAccurate")), analyses[0] if analyses else None)
    if not best or best.get("speed") is None or not best.get("time21_5"):
        return None
    enlil = [e["estimatedShockArrivalTime"] for e in (best.get("enlilList") or [])
             if e.get("estimatedShockArrivalTime")]
    return {
        "id": c["activityID"], "t21": best["time21_5"], "speed": best["speed"],
        "half_angle": best.get("halfAngle"), "lon": best.get("longitude"), "lat": best.get("latitude"),
        "enlil": enlil[0] if enlil else None,
        "linked": [x["activityID"] for x in (c.get("linkedEvents") or [])],
    }


def reduce_ips(r):
    if r.get("location", "Earth") != "Earth":
        return None
    return {"id": r["activityID"], "time": r.get("eventTime") or r["activityID"][:19]}


def month_ranges(start, end):
    for s in pd.date_range(start, end, freq="MS"):
        e = min(s + pd.offsets.MonthEnd(0), pd.Timestamp(end))
        yield s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")


def fetch_month(kind, s, e, reducer):
    f = CACHE / f"{kind}_{s[:7]}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    try:
        raw = get_json(f"{DONKI}/{kind}", params={"startDate": s, "endDate": e}, timeout=120)
    except ValueError:
        print(f"  {kind} {s[:7]}: відповідь не JSON, вважаю порожнім (у кеш не пишу)")
        return []
    reduced = [r for r in (reducer(x) for x in (raw if isinstance(raw, list) else [])) if r]
    f.write_text(json.dumps(reduced, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.5)
    return reduced


cme, ips = [], {}
for s, e in month_ranges("2021-01-01", "2025-12-31"):
    cme += fetch_month("CME", s, e, reduce_cme)
    for r in fetch_month("IPS", s, e, reduce_ips):
        ips[r["id"]] = r["time"]
    print(f"{s[:7]}: CME з аналізом швидкості {len(cme)}, IPS біля Землі {len(ips)}")

rows = []
for c in cme:
    t21 = pd.to_datetime(c["t21"], utc=True)
    obs = None
    for lid in c["linked"]:
        if "-IPS-" in lid and lid in ips:
            h = (pd.to_datetime(ips[lid], utc=True) - t21).total_seconds() / 3600
            if 6 <= h <= 168 and (obs is None or h < obs):
                obs = h
    if obs is None or c["speed"] <= 0:
        continue
    enlil_h = (pd.to_datetime(c["enlil"], utc=True) - t21).total_seconds() / 3600 if c["enlil"] else None
    rows.append({"id": c["id"], "t21": t21, "speed": c["speed"], "half_angle": c["half_angle"],
                 "obs_h": obs, "enlil_h": enlil_h})
ev = pd.DataFrame(rows)
print(f"\nCME із підтвердженим ударом біля Землі: {len(ev)}")

CUT = pd.Timestamp("2024-01-01", tz="UTC")
train, test = ev[ev["t21"] < CUT], ev[ev["t21"] >= CUT]

best = None
for w in (300, 350, 400, 450, 500):
    for g in (0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2):
        pred = train["speed"].apply(lambda v: dbm_hours(v, w=w, gamma=g * 1e-7))
        mae = (pred - train["obs_h"]).abs().mean()
        if best is None or mae < best[0]:
            best = (mae, w, g)
print(f"Калібрування на 2021-2023: w = {best[1]} км/с, gamma = {best[2]}e-7 1/км (MAE {best[0]:.1f} год)")

W, G = best[1], best[2] * 1e-7
ev["const_h"] = ev["speed"].apply(const_speed_hours)
ev["dbm_default_h"] = ev["speed"].apply(dbm_hours)
ev["dbm_cal_h"] = ev["speed"].apply(lambda v: dbm_hours(v, w=W, gamma=G))
train, test = ev[ev["t21"] < CUT], ev[ev["t21"] >= CUT]

METHODS = {"стала швидкість": "const_h", "drag-based (типові параметри)": "dbm_default_h",
           "drag-based (калібровано)": "dbm_cal_h", "ENLIL (NASA)": "enlil_h"}


def report(df, label):
    out = []
    for name, col in METHODS.items():
        d = (df[col] - df["obs_h"]).dropna()
        out.append({"вибірка": label, "метод": name, "n": len(d),
                    "MAE, год": round(d.abs().mean(), 1) if len(d) else None,
                    "медіана |err|, год": round(d.abs().median(), 1) if len(d) else None,
                    "зсув, год": round(d.mean(), 1) if len(d) else None})
    return out


summary = pd.DataFrame(report(ev, "усі") + report(train, "навчання 2021-2023") +
                       report(test, "тест 2024-2025") +
                       report(test.dropna(subset=["enlil_h"]), "тест, де є ENLIL"))
print("\n" + summary.to_string(index=False))

(ROOT / "docs").mkdir(exist_ok=True)
summary.to_csv(ROOT / "docs" / "cme_transit_summary.csv", index=False)
ev.to_csv(CACHE.parent / "cme_events.csv", index=False)