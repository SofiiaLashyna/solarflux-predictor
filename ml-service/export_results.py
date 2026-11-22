import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs"
OUT = HERE.parent / "core-api" / "src" / "main" / "resources" / "static" / "solar_research.json"


def read_csv(name):
    path = DOCS / name
    if not path.exists():
        raise SystemExit(f"Немає {path}: спершу запустіть скрипт, який його створює")
    return pd.read_csv(path)


kp = pd.concat([pd.read_csv(HERE / "data" / f"kp_{y}.csv", index_col=0)["kp"] for y in range(2021, 2026)])
LAGS = [1, 2, 3, 7, 14, 20, 26, 27, 28, 30, 40, 54]
recurrence = {str(d): round(float(kp.autocorr(lag=8 * d)), 3) for d in LAGS}

fs = read_csv("flare_storm_link.csv")
flare_storm = [{"window": r["вікно після піку"], "flares": int(r["спалахів"]),
                "p_after": float(r["P(буря) після спалаху"]), "p_base": float(r["P(буря) база того ж року"]),
                "ratio": float(r["відношення"])} for _, r in fs.iterrows()]

zs = read_csv("flare_zero_shot_results.csv")
flare_models = [{"method": r["метод"], "brier": float(r["Brier"]), "bss": float(r["BSS"]),
                 "auc": float(r["ROC AUC"])} for _, r in zs.iterrows()]

noaa = read_csv("flare_vs_noaa_30d.csv")
columns = [("наша модель", "наша"), ("NOAA, M-клас", "NOAA M"), ("NOAA, M або X", "NOAA M+X"),
           ("частота за 27 діб", "частота 27 діб"), ("кліматологія", "кліматологія")]
flare_vs_noaa = {"days": int(len(noaa)), "event_days": int(noaa["факт"].sum()),
                 "from": str(noaa["доба"].min()), "to": str(noaa["доба"].max()),
                 "brier": {name: round(float(((noaa[col] - noaa["факт"]) ** 2).mean()), 4)
                           for name, col in columns}}

cme = read_csv("cme_transit_summary.csv")
cme = cme[cme["вибірка"] == "тест, де є ENLIL"]
cme_rows = [{"method": r["метод"], "n": int(r["n"]), "mae": float(r["MAE, год"]),
             "median": float(r["медіана |err|, год"]), "bias": float(r["зсув, год"])} for _, r in cme.iterrows()]

payload = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
           "kp_recurrence": recurrence, "flare_storm": flare_storm, "flare_models": flare_models,
           "flare_vs_noaa": flare_vs_noaa, "cme": cme_rows}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
print("Записано", OUT)