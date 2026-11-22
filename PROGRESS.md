## Week 0 (de-risking, before official timeline start)

**Date:** _27.09.2026_

**Done:**
- Set up project repository structure (core-api, ml-service, docs)
- Created Python virtual environment and installed dependencies (PyTorch CPU build, chronos-forecasting, pandas, matplotlib)
- Successfully ran a zero-shot forecast using Chronos-t5-small on a synthetic time series, producing a 24-step forecast with an 80% confidence interval
- Confirmed the core ML pipeline (load pretrained model → predict → visualize) works end-to-end on CPU, with no GPU required

**Issues / not yet done:**
- Real NOAA data (Kp-index, GOES X-ray flux) not yet integrated — currently using synthetic data to validate the pipeline
- Only one model tested so far (Chronos-t5-small); TimesFM 2.5 and Lag-Llama comparison still pending

**Risks for next steps:**
- Real NOAA data may require more cleaning/alignment work than the synthetic baseline suggested
- Model comparison across 3 pretrained models will need a unified evaluation format (same metrics, same test windows)

**Evidence:**
- `demo_forecast_result.png` — forecast plot from first successful zero-shot run

## Week 1

**Date:** _03.10.2026_

**Done:**
- Replaced synthetic data with real Kp-index data from GFZ Potsdam (3-hour resolution, 2021–2025, verified continuous with zero gaps)
- Built a context/test split and ran the first real zero-shot forecast on actual Kp data (not synthetic)
- Implemented rolling-window backtesting: 100 windows, 8-step (24h) forecast horizon, comparing Chronos-t5-small against a persistence baseline
- Result: model MAE 0.901 vs. persistence baseline MAE 1.015 — model beats the baseline on 58% of windows
- Fixed a reproducibility issue (seeded `torch.manual_seed` so results are consistent across runs)

**Issues / not yet done:**
- Only tested on Chronos-t5-small so far; TimesFM and a third model still pending
- Database (Postgres) and Core API not yet connected — ML results currently only live in the Python script, not persisted anywhere
- Confirmation from the professor on TimesFM 2.5 vs TimesFM-3 still pending

**Risks for next steps:**
- Connecting the Java side (Spring Boot + Hibernate + Postgres) introduces a new toolchain (need Docker for Postgres, likely IntelliJ IDEA instead of PyCharm for Java) — first-time setup risk
- Win rate of 58% is only moderately above chance — worth keeping an eye on whether this holds up once a second model is added for comparison

**Evidence:**
- Backtest output showing per-window MAE and the final summary (model vs. baseline vs. win rate)
- `demo_forecast_result.png` — forecast plot with real Kp data and real vs. predicted comparison

## Week 2

**Date:** _13.10_

**Done:**
- Built the Java core-api (Spring Boot 3.3, Hibernate/JPA) with controller → service → repository layers for Observation, Prediction and User
- Ran PostgreSQL in Docker and connected it to the core-api; debugged a port conflict with a system-level PostgreSQL service and a timezone-name mismatch between the JVM and the Postgres container
- Added REST endpoints, including a transactional batch endpoint for observations
- Loaded 14,608 real Kp-index observations (GFZ Potsdam, 2021–2025, 3-hour resolution) into PostgreSQL via a Python script calling the batch endpoint

**Issues / not yet done:**
- Predictions are not yet generated or stored through the API; the ML pipeline still runs standalone
- Kafka, WebSocket, frontend and Docker Compose not started
- No uniqueness constraint on observations (re-running the loader duplicates rows)

**Risks for next steps:**
- Wiring Java and Python together (and later Kafka) is the main integration risk; plan is to close the loop DB → model → DB first
- Only one model compared so far

**Evidence:**
- PostgreSQL row count and sample query output

## Weeks 3–4 (up to 10 Nov 2026)

**Done:**
- Extended the benchmark to three zero-shot models (Chronos-T5-small, Chronos-Bolt-small, TimesFM 2.5) against a persistence baseline: 100 rolling windows spread evenly over 2021–2025, 24 h horizon. MAE / share of windows better than persistence: TimesFM 0.877 / 61%, Bolt 0.890 / 63%, T5 0.951 / 56%, persistence 1.026.
- Added CPU/GPU auto-detection and per-window timing to the benchmark (GPU run still to be done in Colab).
- Core API: scheduled GFZ synchronization (on startup and hourly) with a JDBC batch upsert, a status column (definitive / preliminary) and uniqueness constraints; endpoint for the latest N observations.
- Predictions: redesigned the Prediction entity (model, base time, target time, step, value) and added batch, latest, issue-time and history endpoints; batch writes are idempotent.
- ML microservice (FastAPI) with models preloaded at startup; a Java scheduler calls it automatically when new data arrive, so forecast batches are stored without manual runs.
- Live accuracy report (JDBC join restricted to targets forecast by every model) and a dashboard with history, forecast line, model selector, forecast issue-time selector and backtest-vs-live table.
- Analytics from the database: Kp ≥ 5 intervals per year grew from 26 (2021) to 156 (2025), consistent with the rising phase of solar cycle 25; not claimed as a long-term trend.

**Issues / not yet done:**
- Live accuracy is based on very few points so far; it needs days of automatic runs.
- GPU run and Lag-Llama not done yet.
- Kafka, WebSocket, user subscriptions, Docker Compose and unit tests not started.
- Forecasts mostly follow the recent level; sudden storms cannot be predicted from Kp history alone.

**Next:**
- Accuracy broken down by forecast step, Kafka + WebSocket notifications, rotating-Earth visualization, extra input data (solar wind).

**Evidence:**
- docs/model_comparison_cpu.csv, SQL outputs, dashboard screenshot.

## Weeks 5–7 (10–22 Nov 2026)

**Done:**
- Live accuracy by forecast lead time (JDBC report and chart): each model's error at +3 h … +24 h, computed on stored live forecasts.
- Event-driven pipeline: single-node Kafka broker (Docker Compose); after each forecast batch the core-api publishes a `forecast.created` event, a consumer broadcasts it over WebSocket, and the dashboard refreshes itself without a reload.
- Dashboard: rotating Earth (D3) with an aurora ring whose size follows Kp (observed or forecast, any model, +0 … +24 h), a per-model Kp table, a responsive layout, and a Sun card (see below).
- Repository hygiene: removed superseded scripts, raw datasets excluded from Git, retry logic for HTTP responses that break mid-transfer, `docs/data-sources.md` with licences and credits, `update_ncei.py` that downloads the current-year NCEI flare report.
- Servlet layer: a request-logging filter, an API-key filter for write requests (`X-API-Key`) and a `/health` servlet, with unit tests.
- Strategy and Factory patterns for forecast models: persistence is computed in Java, the other models are called through the ML service, and a failing model no longer blocks the rest; JUnit 5 and Mockito unit tests for the strategies and for `ForecastService` with mocked repositories.
- Solar-flare work (requirement for lab 3):
  - Kp autocorrelation shows a clear 27-day peak (about 0.17 against about 0.06 on neighbouring lags) and a second peak at 54 days, consistent with recurrence from solar rotation.
  - After M/X-class flares (5,277 events, 2000–2025) the probability of Kp ≥ 5 in the following 24 h windows is 0.18 (0–24 h), 0.19 (24–48 h), 0.215 (48–72 h) and 0.20 (72–96 h), against 0.162–0.168 in the two 24 h windows before the flare and a same-year base rate of 0.126. Part of the elevation over the base rate is activity clustering; relative to the window just before the flare the excess is +1.2, +2.3, +4.7 and +3.5 percentage points, peaking at 48–72 h as expected from CME transit times. Flares are not independent events, so no confidence intervals are given.
  - CME arrival time (NASA DONKI, 2021–2025; 5,930 CMEs with a speed estimate, 321 with a linked shock at Earth): constant speed, a drag-based model with typical parameters, the same model calibrated on 2021–2023 (w = 500 km/s, γ = 0.8·10⁻⁷ km⁻¹) and NASA's WSA-ENLIL estimate. Test 2024–2025 (156 events), mean absolute error in hours: 21.0, 15.5, 13.8 and 10.9 (on the 146 events that have an ENLIL estimate: 20.8 / 15.5 / 13.7 / 10.9). This measures arrival time given a hit, not whether a CME hits.
  - Paired bootstrap on those 146 events (events resampled independently, so the intervals are optimistic): calibrated drag-based reduces the constant-speed error by 7.1 h (95% CI 5.0–9.3); calibration instead of typical parameters adds 1.7 h (0.3–3.2), mostly by cutting large errors (the median error did not improve); WSA-ENLIL remains 2.8 h better than the calibrated model (1.3–4.3).
  - Daily full-disk model for the probability of an M+ flare on the current UTC day. Seven flare-history features (flare presence over 1, 3 and 27 days, C+ presence, peak class of the previous day, activity one solar rotation earlier), trained 1996–2019 and tested 2020–Nov 2026: logistic regression Brier 0.141, BSS 0.38, ROC AUC 0.86, against 0.168 / 0.79 for the 27-day flare rate and 0.168 / 0.74 for yesterday's flare. Gradient boosting performs the same and is well calibrated. The previous day's peak class is by far the most informative feature; the sunspot number added almost nothing (BSS 0.392 with it, 0.383 without), and the one-rotation-ago feature is about zero. Features use flare presence and peak class instead of counts because DONKI lists about 10% more M+ flares than NCEI in busy months. The final model is trained on all data and exported as JSON coefficients served by the ML service.
  - Live flare inputs: DONKI turned out to list almost only M/X flares, so the first live probability (0.17%) was an artifact of missing C-class flares. Live features now combine the NCEI yearly flare report with SWPC's 7-day flare list (the two agree on overlapping days) and the service refuses to give a number if the sources leave a gap.
  - Retrospective check against NOAA's official one-day M-class probability over the last 30 days (22 Oct–20 Nov 2026, 6 days with an M+ flare; our model trained only on data up to 2019 to avoid leakage). Brier score: NOAA 0.130 (0.135 for M or X), our logistic model 0.154, climatology 0.160, 27-day flare-rate baseline 0.183. NOAA is slightly ahead and our model is between climatology and NOAA; with six event days the differences are not significant. NOAA's forecasters use active-region information (class, magnetic complexity, growth) that our flare-history features lack.
  - Sun card on the dashboard: the core-api stores a daily flare probability next to NOAA's forecast (scheduler every 6 h), fills in the observed outcome for every pending forecast, and shows a running Brier score on confirmed days.

**Issues / not yet done:**
- Flare forecast: NOAA is slightly better in the 30-day check, and region-level data cannot be used because SWPC's active-region file keeps only ~31 days (archiving it daily would build a history). Live flare accuracy has only a few days so far.
- The live flare features need a recent NCEI file (`update_ncei.py`, run manually for now).
- GPU benchmark (Colab), Lag-Llama, comparison of a pretrained zero-shot model with our regression on daily flare activity, Observer pattern, user subscriptions, full-stack Docker Compose and the final report are still to do.
- PostgreSQL runs in a standalone container without a volume: observations can be re-synchronised from GFZ, but stored forecasts would be lost if the container is removed.

**Next:**
- Observer pattern for stored forecasts; PostgreSQL in Docker Compose with a volume; zero-shot versus regression experiment for flares; GPU run in Colab; final report.

**Evidence:**
- `docs/data-sources.md`, `docs/cme_transit_summary.csv`, `docs/flare_model_results.csv`, `docs/flare_vs_noaa_30d.csv`, `ml-service/flare_storm_link.py`, `ml-service/collect_cme.py`, dashboard screenshots.