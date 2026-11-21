import pandas as pd

from data_loader import get_json

BASE = "https://services.swpc.noaa.gov/json/goes/primary"
for name in ("xray-flares-latest", "xray-flares-7-day"):
    rows = get_json(f"{BASE}/{name}.json", retries=3, timeout=60)
    rows = rows if isinstance(rows, list) else [rows]
    print(f"\n=== {name}: записів {len(rows)}")
    if rows:
        print("поля:", list(rows[0].keys()))
        print("перший запис:", rows[0])

df = pd.DataFrame(get_json(f"{BASE}/xray-flares-7-day.json", retries=3, timeout=60))
col = next((c for c in ("max_class", "class_type", "flare_class", "classType") if c in df.columns), None)
print("\nКолонка класу:", col)
if col:
    print(df[col].astype(str).str[0].value_counts().to_string())