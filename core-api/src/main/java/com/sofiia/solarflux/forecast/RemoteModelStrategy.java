package com.sofiia.solarflux.forecast;

import java.util.List;

public class RemoteModelStrategy implements ForecastStrategy {

    private final String modelName;
    private final MlServiceClient client;

    public RemoteModelStrategy(String modelName, MlServiceClient client) {
        this.modelName = modelName;
        this.client = client;
    }

    @Override
    public String modelName() {
        return modelName;
    }

    @Override
    public List<Double> forecast(List<Double> context, int horizon) {
        return client.forecast(modelName, context, horizon);
    }
}