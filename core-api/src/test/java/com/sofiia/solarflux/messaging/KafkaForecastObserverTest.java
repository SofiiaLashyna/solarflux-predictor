package com.sofiia.solarflux.messaging;

import com.sofiia.solarflux.forecast.ForecastBatch;
import com.sofiia.solarflux.model.Prediction;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;

@ExtendWith(MockitoExtension.class)
class KafkaForecastObserverTest {

    @Mock
    ForecastEventPublisher publisher;

    @Test
    void publishesAForecastCreatedEvent() {
        Instant base = Instant.parse("2026-11-20T12:00:00Z");
        KafkaForecastObserver observer = new KafkaForecastObserver(publisher);

        observer.onForecastsStored(new ForecastBatch(base, List.of(
                new Prediction("a", base, base.plusSeconds(10_800), 1, 1.0),
                new Prediction("b", base, base.plusSeconds(10_800), 1, 2.0))));

        ArgumentCaptor<ForecastCreatedEvent> event = ArgumentCaptor.forClass(ForecastCreatedEvent.class);
        verify(publisher).publish(event.capture());
        assertThat(event.getValue().baseTime()).isEqualTo(base);
        assertThat(event.getValue().models()).containsExactly("a", "b");
        assertThat(event.getValue().count()).isEqualTo(2);
    }
}