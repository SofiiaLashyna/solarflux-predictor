package com.sofiia.solarflux.forecast;

import org.springframework.stereotype.Component;

@Component
public class ForecastStrategyFactory {

    private final MlServiceClient client;

    public ForecastStrategyFactory(MlServiceClient client) {
        this.client = client;
    }

    public ForecastStrategy create(String modelName) {
        if (PersistenceStrategy.NAME.equals(modelName)) {
            return new PersistenceStrategy();
        }
        return new RemoteModelStrategy(modelName, client);
    }
}