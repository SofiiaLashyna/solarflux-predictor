import pandas as pd
import requests

KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"


HEADERS = {"User-Agent": "solarflux-predictor/0.1 (student project)"}


def load_kp_raw() -> pd.DataFrame:
    response = requests.get(KP_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return pd.DataFrame(response.json())

def load_kp_series() -> pd.Series:
    df = load_kp_raw()
    df["time_tag"] = pd.to_datetime(df["time_tag"])
    return df.set_index("time_tag")["estimated_kp"].sort_index()

if __name__ == "__main__":
    series = load_kp_series()
    print(series.describe())
    print(series.index.to_series().diff().value_counts())