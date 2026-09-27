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