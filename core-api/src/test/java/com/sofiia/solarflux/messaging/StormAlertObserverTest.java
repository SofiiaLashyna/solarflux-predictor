package com.sofiia.solarflux.messaging;

import com.sofiia.solarflux.forecast.ForecastBatch;
import com.sofiia.solarflux.model.Prediction;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Duration;
import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;

@ExtendWith(MockitoExtension.class)
class StormAlertObserverTest {

    private static final Instant BASE = Instant.parse("2026-11-20T12:00:00Z");

    @Mock
    ForecastWebSocketHandler webSocketHandler;

    private Prediction prediction(String model, int step, double kp) {
        return new Prediction(model, BASE, BASE.plus(Duration.ofHours(3L * step)), step, kp);
    }

    @Test
    void broadcastsAnAlertWhenAModelPredictsAStorm() {
        StormAlertObserver observer = new StormAlertObserver(webSocketHandler, 5.0);

        observer.onForecastsStored(new ForecastBatch(BASE,
                List.of(prediction("timesfm", 1, 4.0), prediction("timesfm", 2, 5.6))));

        ArgumentCaptor<String> message = ArgumentCaptor.forClass(String.class);
        verify(webSocketHandler).broadcast(message.capture());
        assertThat(message.getValue()).contains("storm.alert").contains("timesfm").contains("5.6");
    }

    @Test
    void staysQuietBelowTheThreshold() {
        StormAlertObserver observer = new StormAlertObserver(webSocketHandler, 5.0);

        observer.onForecastsStored(new ForecastBatch(BASE, List.of(prediction("timesfm", 1, 4.9))));

        verifyNoInteractions(webSocketHandler);
    }

    @Test
    void ignoresThePersistenceBaseline() {
        StormAlertObserver observer = new StormAlertObserver(webSocketHandler, 5.0);

        observer.onForecastsStored(new ForecastBatch(BASE, List.of(prediction("persistence", 1, 7.0))));

        verifyNoInteractions(webSocketHandler);
    }
}