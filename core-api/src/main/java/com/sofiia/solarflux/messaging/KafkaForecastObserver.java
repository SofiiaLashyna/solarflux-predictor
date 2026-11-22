package com.sofiia.solarflux.messaging;

import com.sofiia.solarflux.forecast.ForecastBatch;
import com.sofiia.solarflux.forecast.ForecastObserver;
import org.springframework.stereotype.Component;

@Component
public class KafkaForecastObserver implements ForecastObserver {

    private final ForecastEventPublisher publisher;

    public KafkaForecastObserver(ForecastEventPublisher publisher) {
        this.publisher = publisher;
    }

    @Override
    public void onForecastsStored(ForecastBatch batch) {
        publisher.publish(new ForecastCreatedEvent(batch.baseTime(), batch.models(), batch.predictions().size()));
    }
}