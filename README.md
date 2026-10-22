# SolarFlux Predictor

A space weather forecasting platform that predicts solar flare risk using open
NOAA/NASA data (Kp-index, GOES X-ray flux) and zero-shot foundation models for
time-series forecasting, benchmarked against the official NOAA SWPC forecast.

> This project replaces Labs 1–3 in the "Object-Oriented Programming / Java" course.

## Project Status

🟡 In progress. Current stage: de-risking the ML pipeline (zero-shot inference
with pretrained models). See [PROGRESS.md](./PROGRESS.md) for detailed weekly checkpoints.

## Architecture
```
NOAA data (historical) --> Data Simulator --> Kafka topic: solar.reading
                                                       |
                                                       v
                                                  Core API
                                             (Spring Boot / MVC)
                                                       |
                                                       v
                                                  ML Service
                                              (FastAPI, Python)
                                        Chronos / TimesFM / Lag-Llama
                                              zero-shot forecasting
                                                       |
                              -------------------------------------
                              |                                     |
                              v                                     v
                    PostgreSQL (Hibernate)                 WebSocket --> Frontend
                    users, predictions,                    (React + TypeScript)
                    subscriptions

```
## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Java (LTS), Spring Boot, Spring MVC, Hibernate, JDBC |
| Stream processing | Apache Kafka |
| ML | Python, FastAPI, Chronos-t5-small, TimesFM 2.5, Lag-Llama (zero-shot) |
| Database | PostgreSQL |
| Real-time | WebSocket |
| Frontend | React, TypeScript |
| Infrastructure | Docker, Docker Compose |

## Course Topic Coverage

See [docs/architecture.md](./docs/architecture.md) for the full mapping of
course topics to their implementation in this project.

## Motivation & Research Basis

The official NOAA SWPC forecast (M/X-class solar flares) has been in operation
for years, but Camporeale & Berger (2025) found that over a 26-year evaluation
period, it does not consistently outperform simple statistical baselines
(persistence, climatology) and shows calibration issues. This project benchmarks
several zero-shot foundation models for time-series forecasting against that
same official baseline on open historical data — not to claim novelty as "the
first system of its kind," but to run an honest, measurable comparison against
an existing, imperfect industry solution.
