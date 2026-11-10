import threading
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import compare_models as cm

LOADERS = {
    "chronos-bolt-small": (
        lambda: cm.BaseChronosPipeline.from_pretrained("amazon/chronos-bolt-small", device_map=cm.DEVICE),
        cm.forecast_bolt),
    "timesfm-2.5-200m": (cm.load_timesfm, cm.forecast_timesfm),
    "chronos-t5-small": (
        lambda: cm.ChronosPipeline.from_pretrained("amazon/chronos-t5-small", device_map=cm.DEVICE,
                                                   torch_dtype=cm.torch.float32),
        cm.forecast_t5),
}

loaded = {}
lock = threading.Lock()


@asynccontextmanager
async def lifespan(app):
    for name, (load, fn) in LOADERS.items():
        print(f"Завантажую {name}...")
        loaded[name] = (load(), fn)
    print("Усі моделі готові")
    yield


app = FastAPI(title="SolarFlux ML Service", lifespan=lifespan)


class ForecastRequest(BaseModel):
    context: list[float]
    horizon: int = 8
    models: list[str]


@app.get("/health")
def health():
    return {"status": "ok", "device": cm.DEVICE, "models": ["persistence", *loaded.keys()]}


@app.post("/forecast")
def forecast(req: ForecastRequest):
    ctx = np.asarray(req.context, dtype=np.float64)
    unknown = [m for m in req.models if m != "persistence" and m not in loaded]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Невідомі моделі: {unknown}")
    result = {}
    with lock:
        for name in req.models:
            if name == "persistence":
                result[name] = [float(ctx[-1])] * req.horizon
            else:
                pipe, fn = loaded[name]
                result[name] = [float(v) for v in fn(pipe, ctx, req.horizon)]
    return {"forecasts": result}