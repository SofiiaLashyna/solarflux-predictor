import sys
import numpy as np
import pandas as pd
import requests
import compare_models as cm

API = "http://localhost:8080"
STEP = pd.Timedelta(hours=3)
ISO = "%Y-%m-%dT%H:%M:%SZ"

MODELS = {
    "bolt": ("chronos-bolt-small",
             lambda: cm.BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map=cm.DEVICE),
             cm.forecast_bolt),
    "timesfm": ("timesfm-2.5-200m", cm.load_timesfm, cm.forecast_timesfm),
    "t5": ("chronos-t5-small",
           lambda: cm.ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map=cm.DEVICE,
                                                      torch_dtype=cm.torch.float32),
           cm.forecast_t5),
}


def fetch_context():
    try:
        requests.post(f"{API}/api/sync", timeout=60)   # підтягнути свіжі дані з GFZ
    except requests.RequestException as e:
        print(f"Синхронізація не вдалася ({e}), беру те, що є в базі")
    resp = requests.get(f"{API}/api/observations/latest",
                        params={"type": "KP_INDEX", "limit": cm.CONTEXT}, timeout=30)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    series = df.set_index("timestamp")["value"].sort_index()
    if len(series) < cm.CONTEXT:
        raise SystemExit(f"Недостатньо даних: {len(series)} з {cm.CONTEXT}")
    if (series.index.to_series().diff().dropna() != STEP).any():
        print("Увага: у контексті є пропуски, прогноз менш надійний")
    return series


def main(keys):
    series = fetch_context()
    ctx = series.values
    base = series.index[-1]
    print(f"Контекст до {base:%d.%m %H:%M} UTC, останній Kp = {ctx[-1]:.1f}")

    records = []
    for key in keys:
        if key == "persistence":
            name, pred = "persistence", np.full(cm.HORIZON, ctx[-1])
        else:
            name, load, fn = MODELS[key]
            pred = fn(load(), ctx, cm.HORIZON)
        print(f"{name}: " + ", ".join(f"{v:.1f}" for v in pred))
        for step, value in enumerate(pred, 1):
            records.append({
                "modelName": name,
                "baseTime": base.strftime(ISO),
                "targetTime": (base + STEP * step).strftime(ISO),
                "step": step,
                "predictedValue": round(float(value), 3),
            })

    resp = requests.post(f"{API}/api/predictions/batch", json=records, timeout=30)
    resp.raise_for_status()
    print(f"Збережено прогнозів: {len(records)}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["bolt"])