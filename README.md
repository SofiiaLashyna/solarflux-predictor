# SolarFlux Predictor

A space weather platform that forecasts the geomagnetic Kp index for the next 24 hours with pretrained time-series foundation models (zero-shot), stores every forecast, scores it against what actually happened, and studies how solar flares and coronal mass ejections (CMEs) relate to geomagnetic storms.

> This project replaces Labs 1-3 in the "Object-Oriented Programming / Java" course.

## Status

In progress (updated 20 Nov 2026). The Kp forecasting pipeline, the event-driven live dashboard and the first solar-flare analyses work end to end. Flare probability forecasting, CME transit-time calibration, user subscriptions and the GPU benchmark are still to do. See [PROGRESS.md](./PROGRESS.md) for weekly checkpoints.

## What works today

- **Data:** the Kp index (GFZ Potsdam, 3-hourly) is synchronised on startup and hourly into PostgreSQL; definitive and preliminary values are kept apart (`status`).
- **Forecasting:** a Python microservice (FastAPI) serves Chronos-T5-small, Chronos-Bolt-small and TimesFM 2.5 plus a persistence baseline. The Java core-api requests a 24 h forecast whenever new data arrive and stores each batch.
- **Evaluation:** a backtest on 100 rolling windows spread over 2021-2025, and a live accuracy report that compares stored forecasts with the observed Kp (only on targets forecast by every model), also split by lead time.
- **Live dashboard:** Kp history and forecast per model, a forecast issue-time selector, accuracy tables and charts, and a rotating Earth whose aurora ring follows Kp. New forecasts reach open pages through Kafka and WebSocket without a reload.
- **Solar analysis:** 27-day recurrence of Kp, the link between M/X flares and storms, a drag-based CME arrival-time estimate (see below).

## Results so far

Backtest, 24 h horizon, 100 windows over 2021-2025 (CPU):

| Model | MAE (Kp) | Better than persistence |
|---|---|---|
| TimesFM 2.5 | 0.877 | 61% of windows |
| Chronos-Bolt-small | 0.890 | 63% of windows |
| Chronos-T5-small | 0.951 | 56% of windows |
| Persistence (baseline) | 1.026 | - |

The forecasts mostly follow the recent level; sudden storms cannot be predicted from Kp history alone. Live accuracy needs more days of automatic forecasts before it means much.

### Solar flares and storms (in progress)

- Kp autocorrelation (2021-2025) has a clear peak at 27 days (about 0.17 against about 0.06 on neighbouring lags) and a second one at 54 days, consistent with recurrence from solar rotation.
- After M/X-class flares (5,277 events, 2000-2025) the chance of Kp >= 5 in the following 24 h windows is 1.4-1.7 times the same-year base rate, highest 48-72 h after the flare, which fits CME travel times.
- A drag-based CME transit-time model is implemented and compared with a constant-speed estimate and NASA's WSA-ENLIL estimate on one event (May 2024). Calibration on 2021-2025 CMEs is next.

## Architecture

```text
GFZ Kp index --(hourly sync, JDBC upsert)--> PostgreSQL <--> Core API (Spring Boot, Hibernate)
                                                                  |
                                      new observations (scheduler)|
                                                                  v
                          ML Service (FastAPI: Chronos-T5, Chronos-Bolt, TimesFM 2.5, persistence)
                                                                  |
                                                  forecasts       v
                                      predictions table <---- Core API
                                                                  |
                                          Kafka topic: forecast.created
                                                                  |
                                                  consumer --> WebSocket
                                                                  |
                                                                  v
                       Dashboard (HTML/JS, Chart.js, D3): history, forecast, accuracy, rotating Earth
```

## Tech stack

| Layer | Technologies |
|---|---|
| Backend | Java 21, Spring Boot 3.3, Spring MVC, Hibernate/JPA, JDBC |
| Messaging | Apache Kafka (single-node KRaft broker via Docker Compose), WebSocket |
| ML | Python, FastAPI, PyTorch (CPU build), chronos-forecasting, timesfm |
| Database | PostgreSQL 16 (Docker) |
| Frontend | HTML/JS, Chart.js, D3 |
| Infrastructure | Docker, Docker Compose (PostgreSQL and Kafka |

## Running locally (Windows, PowerShell)

```powershell
# 1. Database and Kafka (PostgreSQL data lives in the named volume solarflux-pgdata)
docker compose up -d

# 2. ML service (in ml-service, with a Python virtual environment)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m uvicorn forecast_service:app --host 127.0.0.1 --port 8000

# 3. Core API: run SolarFluxApplication from IntelliJ (or mvn spring-boot:run in core-api)
# 4. Open http://localhost:8080
```

## Data sources

Raw datasets are not stored in the repository. See [docs/data-sources.md](./docs/data-sources.md) for the sources, licences and credits (Kp index: GFZ Potsdam, CC BY 4.0, Matzka et al., 2021, doi:10.5880/Kp.0001; sunspot number: WDC-SILSO, Royal Observatory of Belgium, Brussels).

## Course topic coverage

| Topic | Status |
|---|---|
| Spring, MVC, REST | done |
| Hibernate / JPA, PostgreSQL | done |
| Transactions, ACID | done (transactional batch writes) |
| JDBC | done (batch upsert, accuracy reports) |
| Kafka | done (`forecast.created`) |
| WebSocket | done |
| Microservices | done (Java core-api + Python ML service) |
| Multithreading | partial (scheduled background jobs, locks) |
| Docker | partial (Kafka in Compose, PostgreSQL standalone) |
| SPA | partial (plain HTML/JS) |
| GoF patterns (Strategy, Factory, Observer) | done |
| Servlets (filters, servlet), unit tests | done |

## Repository structure

```text
core-api/    Spring Boot backend (REST, sync, scheduler, Kafka, WebSocket, static dashboard)
ml-service/  Python: forecast microservice, benchmark, solar-data analysis scripts
docs/        Data sources, screenshots, benchmark tables
PROGRESS.md  Weekly checkpoints
```

## Motivation

Geomagnetic storms disturb satellites, radio, navigation and power grids, and Kp is the standard 3-hourly index of their strength. Instead of training a model from scratch, this project evaluates recent pretrained foundation models for time series against simple baselines on open data, and checks them on live forecasts the system stores itself. Claims are deliberately modest: the goal is an honest, measurable comparison.