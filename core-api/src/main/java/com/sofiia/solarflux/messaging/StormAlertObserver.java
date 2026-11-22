package com.sofiia.solarflux.messaging;

import com.sofiia.solarflux.forecast.ForecastBatch;
import com.sofiia.solarflux.forecast.ForecastObserver;
import com.sofiia.solarflux.forecast.PersistenceStrategy;
import com.sofiia.solarflux.model.Prediction;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Comparator;
import java.util.Locale;

@Component
public class StormAlertObserver implements ForecastObserver {

    private static final Logger log = LoggerFactory.getLogger(StormAlertObserver.class);

    private final ForecastWebSocketHandler webSocketHandler;
    private final double threshold;

    public StormAlertObserver(ForecastWebSocketHandler webSocketHandler,
                              @Value("${alerts.storm-threshold:5.0}") double threshold) {
        this.webSocketHandler = webSocketHandler;
        this.threshold = threshold;
        log.info("Поріг попередження про бурю: Kp >= {}", threshold);
    }

    @Override
    public void onForecastsStored(ForecastBatch batch) {
        batch.predictions().stream()
                .filter(p -> !PersistenceStrategy.NAME.equals(p.getModelName()))
                .max(Comparator.comparingDouble(Prediction::getPredictedValue))
                .filter(p -> p.getPredictedValue() >= threshold)
                .ifPresent(p -> {
                    log.warn("Попередження про бурю: {} очікує Kp ≈ {} на {}",
                            p.getModelName(), p.getPredictedValue(), p.getTargetTime());
                    webSocketHandler.broadcast(String.format(Locale.ROOT,
                            "{\"type\":\"storm.alert\",\"data\":{\"model\":\"%s\",\"kp\":%.1f,\"targetTime\":\"%s\"}}",
                            p.getModelName(), p.getPredictedValue(), p.getTargetTime()));
                });
    }
}