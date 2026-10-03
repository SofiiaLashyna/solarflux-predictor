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