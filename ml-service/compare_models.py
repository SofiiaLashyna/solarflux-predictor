import numpy as np
import pandas as pd
import torch
from pathlib import Path
from chronos import BaseChronosPipeline, ChronosPipeline
from data_loader import load_kp_gfz

torch.manual_seed(42)

ROOT = Path(__file__).resolve().parent.parent
CONTEXT = 512
HORIZON = 8          
MAX_WINDOWS = 100


def forecast_t5(pipeline, ctx, horizon):
    samples = pipeline.predict(torch.tensor(ctx), prediction_length=horizon, num_samples=20)
    return np.median(samples[0].numpy(), axis=0)


def forecast_bolt(pipeline, ctx, horizon):
    quantiles, _ = pipeline.predict_quantiles(
        [torch.tensor(ctx, dtype=torch.float32)],
        prediction_length=horizon,
        quantile_levels=[0.5],
    )
    return quantiles[0, :, 0].numpy()


def run():
    values = load_kp_gfz("2021-01-01T00:00:00Z", "2025-12-31T23:59:59Z").values

    print("Завантажую моделі...")
    models = {
        "chronos-t5-small": (
            ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map="cpu", torch_dtype=torch.float32),
            forecast_t5,
        ),
        "chronos-bolt-small": (
            BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map="cpu"),
            forecast_bolt,
        ),
    }
    errors = {name: [] for name in models}
    errors["persistence"] = []

    step = (len(values) - CONTEXT - HORIZON) // MAX_WINDOWS   # вікна рівномірно по всіх 5 роках
    starts = list(range(CONTEXT, len(values) - HORIZON, step))[:MAX_WINDOWS]

    for i, s in enumerate(starts, 1):
        ctx = values[s - CONTEXT:s]
        actual = values[s:s + HORIZON]
        errors["persistence"].append(np.mean(np.abs(ctx[-1] - actual)))
        for name, (pipe, fn) in models.items():
            errors[name].append(np.mean(np.abs(fn(pipe, ctx, HORIZON) - actual)))
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
        })
    table = pd.DataFrame(rows).sort_values("MAE")
    print(table.to_string(index=False))

    (ROOT / "docs").mkdir(exist_ok=True)
    table.to_csv(ROOT / "docs" / "model_comparison.csv", index=False)
    static = ROOT / "core-api" / "src" / "main" / "resources" / "static"
    static.mkdir(parents=True, exist_ok=True)
    table.to_json(static / "model_comparison.json", orient="records", force_ascii=False)


if __name__ == "__main__":
    run()