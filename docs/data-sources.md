# Data sources

Raw datasets are not stored in the repository (`ml-service/data/` is listed in `.gitignore`). Download them as described below and place them in `ml-service/data/`.

| Data | Source | License / credit | Used by |
|---|---|---|---|
| Kp index (3-hourly) | GFZ Helmholtz Centre Potsdam web service, https://kp.gfz.de | CC BY 4.0; cite Matzka et al. (2021), DOI 10.5880/Kp.0001 | core-api sync, `ml-service/data_loader.py` |
| Solar flare list (GOES, 1995 to now) | NOAA NCEI GOES flare report (mission-length CSV), https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/multi/l2/data/xrsf-l2-flrpt_science/ | NOAA public data | `flare_storm_link.py` |
| Daily total sunspot number | WDC-SILSO, Royal Observatory of Belgium, Brussels, https://www.sidc.be/SILSO/datafiles (`SN_d_tot_V2.0.csv`) | CC BY-NC; credit: "Source: WDC-SILSO, Royal Observatory of Belgium, Brussels" | planned flare model |
| CMEs, geomagnetic storms, shocks | NASA CCMC DONKI, https://ccmc.gsfc.nasa.gov/DONKI-API/get/ | public NASA data | `cme_transit.py` |
| Active regions, official flare probabilities | NOAA SWPC JSON services, https://services.swpc.noaa.gov/json/ | NOAA public data | `explore_solar.py` |