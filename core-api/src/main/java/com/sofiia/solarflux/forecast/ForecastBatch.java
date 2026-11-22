package com.sofiia.solarflux.forecast;

import com.sofiia.solarflux.model.Prediction;

import java.time.Instant;
import java.util.List;

public record ForecastBatch(Instant baseTime, List<Prediction> predictions) {

    public List<String> models() {
        return predictions.stream().map(Prediction::getModelName).distinct().toList();
    }
}