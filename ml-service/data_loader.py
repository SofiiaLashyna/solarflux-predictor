import pandas as pd
import requests
import time
import io

KP_URL = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
GFZ_URL = "https://kp.gfz.de/app/json/"
SILSO_URL = "https://www.sidc.be/SILSO/INFO/sndtotcsv.php"

HEADERS = {"User-Agent": "solarflux-predictor/0.1 (student project)"}

SILSO_COLS = ["year", "month", "day", "decimal_year", "ssn", "ssn_std", "n_obs", "provisional"]


def load_ssn():
    """Щоденне число плям WDC-SILSO; значення -1 (немає даних) прибрано."""
    response = requests.get(SILSO_URL, headers=HEADERS, timeout=60)
    response.raise_for_status()
    if not response.text[:4].strip().isdigit():
        raise ValueError("SILSO повернув не CSV: " + response.text[:80])
    df = pd.read_csv(io.StringIO(response.text), sep=";", names=SILSO_COLS)
    df["date"] = pd.to_datetime(df[["year", "month", "day"]])
    return df[df["ssn"] >= 0].set_index("date")["ssn"]

def load_kp_gfz(start: str, end: str, definitive_only: bool = True) -> pd.Series:
    params = {"start": start, "end": end, "index": "Kp"}
    if definitive_only:
        params["status"] = "def"
    data = get_json(GFZ_URL, params)

    series = pd.Series(
        data["Kp"],
        index=pd.to_datetime(data["datetime"]),
        name="kp",
    )
    return series[series >= 0].sort_index()

def get_json(url, params=None, retries=5, timeout=60):
    last = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code < 500:
                raise          # 4xx повторювати марно
            last = e
        except (requests.RequestException, ValueError) as e:
            last = e
        time.sleep(2 * attempt)
    raise last

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