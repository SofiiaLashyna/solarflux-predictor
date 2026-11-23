import json
from pathlib import Path

from data_loader import get_json

OUT = Path(__file__).resolve().parent.parent / "core-api" / "src" / "main" / "resources" / "static" / "sun_regions.json"
rows = get_json("https://services.swpc.noaa.gov/json/solar_regions.json", retries=3, timeout=60)
keep = ["observed_date", "region", "latitude", "longitude", "area", "spot_class", "mag_class",
        "number_spots", "m_flare_probability", "x_flare_probability"]
data = [{k: r.get(k) for k in keep} for r in rows
        if r.get("latitude") is not None and r.get("longitude") is not None]
OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
print(len(data), "записів, діб:", len({r["observed_date"] for r in data}))