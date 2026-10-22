import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
from chronos import ChronosPipeline
from data_loader import load_kp_gfz

torch.manual_seed(42)

def run_zero_shot_forecast():
    print("Завантажую Chronos-t5-small...")
    pipeline = ChronosPipeline.from_pretrained(
        "amazon/chronos-t5-small",
        device_map="cpu",
        torch_dtype=torch.float32,
    )
    kp = load_kp_gfz("2021-01-01T00:00:00Z", "2025-12-31T23:59:59Z")

    context_length = 512
    prediction_length = 8

    context_series = kp.iloc[-(context_length + prediction_length):-prediction_length]
    actual_future = kp.iloc[-prediction_length:]

    series = context_series.values
    context = torch.tensor(series)

    print(f"Роблю прогноз на {prediction_length} кроків вперед...")
    forecast = pipeline.predict(
        context,
        prediction_length=prediction_length,
        num_samples=20,
    )
    forecast_values = forecast[0].numpy()
    low, median, high = np.quantile(forecast_values, [0.1, 0.5, 0.9], axis=0)

    mae = np.mean(np.abs(median - actual_future.values))
    print(f"MAE (середня абсолютна помилка): {mae:.3f}")

    persistence_forecast = np.full(prediction_length, context_series.values[-1])
    persistence_mae = np.mean(np.abs(persistence_forecast - actual_future.values))
    print(f"MAE базлайну (persistence): {persistence_mae:.3f}")

    plt.figure(figsize=(10, 5))
    plt.plot(range(len(series)), series, label="Історичні дані (Kp)")

    forecast_index = range(len(series), len(series) + len(median))
    plt.plot(forecast_index, median, label="Прогноз (медіана)", color="tab:orange")
    plt.plot(forecast_index, actual_future.values, label="Реальні дані", color="tab:green", linestyle="--")
    plt.fill_between(forecast_index, low, high, alpha=0.3, color="tab:orange",
                      label="80% довірчий інтервал")

    plt.legend()
    plt.title(f"Zero-shot прогноз Kp: Chronos-t5-small ({prediction_length * 3} год вперед)")
    plt.savefig("../docs/screenshots/demo_forecast_result.png", dpi=150)
    print("Готово! Результат у demo_forecast_result.png")
    return kp, pipeline

def backtest(kp, pipeline, context_length=512, prediction_length=8, step_days=7, max_windows=100):
    step = step_days * 8  # 8 точок на добу (крок 3 год)
    model_errors = []
    persistence_errors = []

    total_points = len(kp)
    start_indices = range(context_length, total_points - prediction_length, step)

    for i, start in enumerate(start_indices):
        if i >= max_windows:
            break

        context_series = kp.iloc[start - context_length:start]
        actual_future = kp.iloc[start:start + prediction_length]

        context = torch.tensor(context_series.values)
        forecast = pipeline.predict(context, prediction_length=prediction_length, num_samples=20)
        median = np.quantile(forecast[0].numpy(), 0.5, axis=0)

        model_mae = np.mean(np.abs(median - actual_future.values))
        persistence_forecast = np.full(prediction_length, context_series.values[-1])
        persistence_mae = np.mean(np.abs(persistence_forecast - actual_future.values))

        model_errors.append(model_mae)
        persistence_errors.append(persistence_mae)

        print(f"Вікно {i+1}: модель={model_mae:.3f}, персистентність={persistence_mae:.3f}")

    print(f"\nСереднє MAE моделі: {np.mean(model_errors):.3f}")
    print(f"Середнє MAE персистентності: {np.mean(persistence_errors):.3f}")
    win_rate = np.mean(np.array(model_errors) < np.array(persistence_errors))
    print(f"Модель краща за персистентність у {win_rate:.1%} вікон")

if __name__ == "__main__":
    kp, pipeline = run_zero_shot_forecast()
    print("\n--- Backtest на багатьох вікнах ---")
    backtest(kp, pipeline)