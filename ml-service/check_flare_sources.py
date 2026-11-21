from pathlib import Path

import pandas as pd

from data_loader import get_json

DATA = Path(__file__).resolve().parent / "data"
ncei = pd.read_csv(next(DATA.glob("sci_xrsf-l2-flrpt_geo_s1995*.csv")), usecols=["time", "flare_class"])
ncei["time"] = pd.to_datetime(ncei["time"], utc=True)
ncei = ncei[(ncei["time"] >= pd.Timestamp("2024-01-01", tz="UTC")) &
            (ncei["time"] < pd.Timestamp("2025-01-01", tz="UTC")) &
            ncei["flare_class"].astype(str).str[0].isin(["M", "X"])]
ncei_m = ncei.groupby(ncei["time"].dt.month).size()

rows = []
for month in range(1, 13):
    s = f"2024-{month:02d}-01"
    e = (pd.Timestamp(s) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
    raw = get_json("https://ccmc.gsfc.nasa.gov/DONKI-API/get/FLR",
                   params={"startDate": s, "endDate": e}, timeout=120)
    raw = raw if isinstance(raw, list) else []
    donki = sum(1 for f in raw if str(f.get("classType", ""))[:1] in ("M", "X"))
    rows.append({"місяць": month, "NCEI M+": int(ncei_m.get(month, 0)), "DONKI M+": donki})
print(pd.DataFrame(rows).to_string(index=False))