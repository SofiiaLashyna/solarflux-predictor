package com.sofiia.solarflux.forecast;

public interface ForecastObserver {

    void onForecastsStored(ForecastBatch batch);
}