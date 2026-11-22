package com.sofiia.solarflux.forecast;

import java.util.Collections;
import java.util.List;

public class PersistenceStrategy implements ForecastStrategy {

    public static final String NAME = "persistence";

    @Override
    public String modelName() {
        return NAME;
    }

    @Override
    public List<Double> forecast(List<Double> context, int horizon) {
        if (context.isEmpty()) {
            throw new IllegalArgumentException("Порожній контекст");
        }
        return Collections.nCopies(horizon, context.get(context.size() - 1));
    }
}