package com.sofiia.solarflux.forecast;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;

class ForecastStrategyFactoryTest {

    private final ForecastStrategyFactory factory = new ForecastStrategyFactory(mock(MlServiceClient.class));

    @Test
    void createsLocalStrategyForPersistence() {
        assertThat(factory.create("persistence")).isInstanceOf(PersistenceStrategy.class);
    }

    @Test
    void createsRemoteStrategyForOtherModels() {
        ForecastStrategy strategy = factory.create("chronos-bolt-small");

        assertThat(strategy).isInstanceOf(RemoteModelStrategy.class);
        assertThat(strategy.modelName()).isEqualTo("chronos-bolt-small");
    }
}