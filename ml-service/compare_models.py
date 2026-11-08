import numpy as np
import pandas as pd
import torch

import timesfm
from pathlib import Path
from chronos import BaseChronosPipeline, ChronosPipeline
from data_loader import load_kp_gfz

torch.manual_seed(42)

import time
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Пристрій: {DEVICE}")

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = 512
HORIZON = 8
MAX_WINDOWS = 100


def forecast_t5(pipeline, ctx, horizon):
    samples = pipeline.predict(torch.tensor(ctx), prediction_length=horizon, num_samples=20)
    return np.median(samples[0].cpu().numpy(), axis=0)


def forecast_bolt(pipeline, ctx, horizon):
    quantiles, _ = pipeline.predict_quantiles(
        [torch.tensor(ctx, dtype=torch.float32)],
        prediction_length=horizon,
        quantile_levels=[0.5],
    )
    return quantiles[0, :, 0].cpu().numpy()

def load_timesfm():
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
    model.compile(timesfm.ForecastConfig(
        max_context=1024,
        max_horizon=256,
        normalize_inputs=True,
        use_continuous_quantile_head=True,
        force_flip_invariance=True,
        infer_is_positive=True,
        fix_quantile_crossing=True,
    ))
    return model


def forecast_timesfm(model, ctx, horizon):
    point, _ = model.forecast(horizon=horizon, inputs=[ctx.astype(np.float32)])
    return np.asarray(point[0])

def run():
    values = load_kp_gfz("2021-01-01T00:00:00Z", "2025-12-31T23:59:59Z").values

    print("Завантажую моделі...")
    models = {
        "chronos-t5-small": (
            ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map=DEVICE, torch_dtype=torch.float32),
            forecast_t5,
        ),
        "chronos-bolt-small": (
            BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map=DEVICE),
            forecast_bolt,
        ),
        "timesfm-2.5-200m": (load_timesfm(), forecast_timesfm),
    }
    errors = {name: [] for name in models}
    errors["persistence"] = []

    step = (len(values) - CONTEXT - HORIZON) // MAX_WINDOWS   # вікна рівномірно по всіх 5 роках
    starts = list(range(CONTEXT, len(values) - HORIZON, step))[:MAX_WINDOWS]
    timings = {name: 0.0 for name in models}

    for i, s in enumerate(starts, 1):
        ctx = values[s - CONTEXT:s]
        actual = values[s:s + HORIZON]
        errors["persistence"].append(np.mean(np.abs(ctx[-1] - actual)))
        for name, (pipe, fn) in models.items():
            t0 = time.perf_counter()
            pred = fn(pipe, ctx, HORIZON)
            timings[name] += time.perf_counter() - t0
            errors[name].append(np.mean(np.abs(pred - actual)))
        if i % 10 == 0:
            print(f"Вікно {i}/{len(starts)}")

    base = np.array(errors["persistence"])
    rows = []
    for name, errs in errors.items():
        errs = np.array(errs)
        rows.append({
            "model": name,
            "MAE": round(float(errs.mean()), 3),
            "beats_persistence_%": None if name == "persistence" else round(float(100 * (errs < base).mean()), 1),
            "ms_per_window": None if name == "persistence" else round(1000 * timings[name] / len(starts), 1),
            "device": DEVICE,
        })
    table = pd.DataFrame(rows).sort_values("MAE")
    print(table.to_string(index=False))

    (ROOT / "docs").mkdir(exist_ok=True)
    table.to_csv(ROOT / "docs" / f"model_comparison_{DEVICE}.csv", index=False)
    static = ROOT / "core-api" / "src" / "main" / "resources" / "static"
    static.mkdir(parents=True, exist_ok=True)
    table.to_json(static / "model_comparison.json", orient="records", force_ascii=False)


if __name__ == "__main__":
    run()