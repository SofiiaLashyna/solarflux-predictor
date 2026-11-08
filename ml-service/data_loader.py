import pandas as pd
import requests

KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"


GFZ_URL = "https://kp.gfz.de/app/json/"


HEADERS = {"User-Agent": "solarflux-predictor/0.1 (student project)"}

# Obsolete
def load_kp_raw() -> pd.DataFrame:
    response = requests.get(KP_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json())

def load_kp_series() -> pd.Series:
    df = load_kp_raw()
    df["time_tag"] = pd.to_datetime(df["time_tag"])
    return df.set_index("time_tag")["estimated_kp"].sort_index()

# New
def load_kp_gfz(start: str, end: str, definitive_only: bool = True) -> pd.Series:
    params = {"start": start, "end": end, "index": "Kp"}
    if definitive_only:
        params["status"] = "def"
    response = requests.get(GFZ_URL, params=params, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()

    series = pd.Series(
        data["Kp"],
        index=pd.to_datetime(data["datetime"]),
        name="kp",
    )
    return series[series >= 0].sort_index()

if __name__ == "__main__":
    kp = load_kp_gfz("2021-01-01T00:00:00Z", "2025-12-31T23:59:59Z")
    print(kp.shape)
    print(kp.describe())
    print(kp.index.to_series().diff().value_counts())

    context_length = 512
    prediction_length = 8

    context = kp.iloc[-(context_length + prediction_length):-prediction_length]
    actual_future = kp.iloc[-prediction_length:]

    print("Контекст:", context.shape, context.index.min(), "→", context.index.max())
    print("Що насправді сталось:", actual_future.shape, actual_future.index.min(), "→", actual_future.index.max())
    print(actual_future)