import pandas as pd

from flare_live import ncei_events, swpc_events

swpc = swpc_events()
swpc["day"] = pd.to_datetime(swpc["day"])
ncei = ncei_events(swpc["day"].min())


def daily(df):
    return df.groupby("day").agg(n=("flux", "size"), max_flux=("flux", "max"))


both = daily(ncei).join(daily(swpc), how="inner", lsuffix="_ncei", rsuffix="_swpc")
both["відношення потоків"] = both["max_flux_swpc"] / both["max_flux_ncei"]
print(both.to_string())