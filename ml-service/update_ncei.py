import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests

from data_loader import HEADERS

BASE = "https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/csv/"
LIVE = Path(__file__).resolve().parent / "data" / "live"
LIVE.mkdir(parents=True, exist_ok=True)

html = requests.get(BASE, headers=HEADERS, timeout=60).text
links = re.findall(r'href="([^"?#]+)"', html)


def find_year_file(year):
    pattern = re.compile(rf"sci_xrsf-l2-flrpt_geo_y{year}_v[\d-]+\.csv$")
    for link in links:
        name = link.rsplit("/", 1)[-1]
        if pattern.search(name):
            return name, urljoin(BASE, link)
    return None


def download(year, force):
    found = find_year_file(year)
    if not found:
        print(f"Файл за {year} рік не знайдено")
        return
    name, url = found
    target = LIVE / name
    if target.exists() and not force:
        print("Уже є:", name)
        return
    part = target.with_suffix(".part")
    with requests.get(url, headers=HEADERS, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(part, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    part.replace(target)
    for old in LIVE.glob(f"sci_xrsf-l2-flrpt_geo_y{year}_v*.csv"):
        if old != target:
            old.unlink()
    last = pd.read_csv(target, usecols=["time"])["time"].max()
    print(f"Оновлено {name}, остання подія: {last}")


year = date.today().year
download(year - 1, force=False)
download(year, force=True)