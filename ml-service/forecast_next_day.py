import sys
from datetime import datetime, timedelta, timezone
import pandas as pd
from data_loader import load_kp_gfz
import compare_models as cm

MODEL = sys.argv[1] if len(sys.argv) > 1 else "timesfm"   # timesfm | bolt | t5

if MODEL == "timesfm":
    pipe, fn = cm.load_timesfm(), cm.forecast_timesfm
elif MODEL == "bolt":
    pipe = cm.BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map=cm.DEVICE)
    fn = cm.forecast_bolt
else:
    pipe = cm.ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map=cm.DEVICE,
                                              torch_dtype=cm.torch.float32)
    fn = cm.forecast_t5

fmt = "%Y-%m-%dT%H:%M:%SZ"
end = datetime.now(timezone.utc)
kp = load_kp_gfz((end - timedelta(days=75)).strftime(fmt), end.strftime(fmt), definitive_only=False)

steps = kp.index.to_series().diff().dropna()
if (steps != pd.Timedelta(hours=3)).any():
    print("Увага: у даних є пропуски, прогноз менш надійний")

ctx = kp.values[-cm.CONTEXT:]
pred = fn(pipe, ctx, cm.HORIZON)

last = kp.index[-1]
print(f"Модель: {MODEL}. Останнє відоме значення: {last:%d.%m %H:%M} UTC, Kp = {kp.iloc[-1]:.1f}")
for i, v in enumerate(pred, 1):
    t = last + pd.Timedelta(hours=3 * i)
    print(f"{t.tz_convert('Europe/Kyiv'):%d.%m %H:%M} (Київ, початок 3-годинного інтервалу)   Kp ≈ {v:.1f}")