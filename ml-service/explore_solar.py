
import pandas as pd

from data_loader import load_kp_gfz, get_json

HEADERS = {"User-Agent": "solarflux-predictor/0.1 (student project)"}


def get(url, **params):
    return get_json(url, params=params, timeout=90)


def show(title, records):
    if isinstance(records, dict):
        records = [records]
    print(f"\n=== {title} ===")
    print("записів:", len(records))
    if records:
        print("поля:", list(records[0].keys()))
        print("перший запис:", str(records[0])[:600])


DONKI = "https://ccmc.gsfc.nasa.gov/DONKI-API/get"
for name in ("FLR", "GST", "CME"):
    try:
        show(f"DONKI {name}, травень 2024",
             get(f"{DONKI}/{name}", startDate="2024-05-01", endDate="2024-05-31"))
    except Exception as e:
        print(f"\n=== DONKI {name}: помилка: {e}")

for name in ("solar_regions", "solar_probabilities"):
    try:
        show(f"SWPC {name}", get(f"https://services.swpc.noaa.gov/json/{name}.json"))
    except Exception as e:
        print(f"\n=== SWPC {name}: помилка: {e}")

kp = load_kp_gfz("2021-01-01T00:00:00Z", "2025-12-31T23:59:59Z")
acf = pd.Series({d: kp.autocorr(lag=8 * d) for d in range(1, 61)})
print("\n=== Автокореляція Kp (лаг у добах) ===")
print(acf.loc[[1, 2, 3, 7, 14, 20, 26, 27, 28, 30, 40, 54]].round(3).to_string())
print("Найвищий пік серед лагів 20–35 діб:", acf.loc[20:35].idxmax(), "діб")