from pathlib import Path

import numpy as np
import pandas as pd

ev = pd.read_csv(Path(__file__).resolve().parent / "data" / "cme_events.csv")
ev["t21"] = pd.to_datetime(ev["t21"], utc=True)
test = ev[ev["t21"] >= pd.Timestamp("2024-01-01", tz="UTC")].dropna(subset=["enlil_h"])
rng = np.random.default_rng(42)


def boot(a, b, n=5000):
    diff = (test[a] - test["obs_h"]).abs().values - (test[b] - test["obs_h"]).abs().values
    means = [rng.choice(diff, len(diff)).mean() for _ in range(n)]
    return diff.mean(), np.percentile(means, [2.5, 97.5])


print(f"Тест 2024-2025 з оцінкою ENLIL, n = {len(test)}")
print("Δ MAE = (похибка першого) - (похибка другого); плюс означає, що другий метод кращий\n")
for a, b in [("const_h", "dbm_cal_h"), ("dbm_default_h", "dbm_cal_h"), ("dbm_cal_h", "enlil_h")]:
    m, ci = boot(a, b)
    print(f"{a:14s} -> {b:10s}: Δ = {m:+.1f} год, 95% ДІ [{ci[0]:+.1f}, {ci[1]:+.1f}]")