import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from chronos import ChronosPipeline

def make_synthetic_series(n_points=200):
    rng = np.random.default_rng(42)
    trend = np.sin(np.linspace(0, 8 * np.pi, n_points)) * 3 + 5
    noise = rng.normal(0, 0.5, n_points)
    flares = rng.choice([0, 0, 0, 0, 4], size=n_points)
    return trend + noise + flares

def run_zero_shot_forecast():
    print("Завантажую Chronos-t5-small...")
    pipeline = ChronosPipeline.from_pretrained(
        "amazon/chronos-t5-small",
        device_map="cpu",
        torch_dtype=torch.float32,
    )
    series = make_synthetic_series()
    context = torch.tensor(series)

    print("Роблю прогноз на 24 кроки вперед...")
    forecast = pipeline.predict(
        context,
        prediction_length=24,
        num_samples=20,
    )
    forecast_values = forecast[0].numpy()
    low, median, high = np.quantile(forecast_values, [0.1, 0.5, 0.9], axis=0)
    plt.figure(figsize=(10, 5))
    plt.plot(range(len(series)), series, label="Історичні дані (синтетичні)")

    forecast_index = range(len(series), len(series) + len(median))
    plt.plot(forecast_index, median, label="Прогноз (медіана)", color="tab:orange")
    plt.fill_between(forecast_index, low, high, alpha=0.3, color="tab:orange",
                      label="80% довірчий інтервал")

    plt.legend()
    plt.title("Zero-shot прогноз: Chronos-t5-small")
    plt.savefig("demo_forecast_result.png", dpi=150)
    print("Готово! Результат у demo_forecast_result.png")

if __name__ == "__main__":
    run_zero_shot_forecast()