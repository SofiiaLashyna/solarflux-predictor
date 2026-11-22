package com.sofiia.solarflux.service;

import com.sofiia.solarflux.forecast.ForecastStrategy;
import com.sofiia.solarflux.forecast.PersistenceStrategy;
import com.sofiia.solarflux.messaging.ForecastCreatedEvent;
import com.sofiia.solarflux.messaging.ForecastEventPublisher;
import com.sofiia.solarflux.model.Observation;
import com.sofiia.solarflux.model.Prediction;
import com.sofiia.solarflux.repository.ObservationRepository;
import com.sofiia.solarflux.repository.PredictionRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Pageable;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ForecastServiceTest {

    private static final Instant NEWEST = Instant.parse("2026-11-20T12:00:00Z");
    private static final Duration STEP = Duration.ofHours(3);
    private static final int CONTEXT = 4;
    private static final int HORIZON = 2;

    @Mock
    ObservationRepository observationRepository;
    @Mock
    PredictionRepository predictionRepository;
    @Mock
    PredictionService predictionService;
    @Mock
    ForecastEventPublisher eventPublisher;
    @Captor
    ArgumentCaptor<List<Prediction>> predictionsCaptor;
    @Captor
    ArgumentCaptor<ForecastCreatedEvent> eventCaptor;

    private record FakeStrategy(String modelName, List<Double> values, boolean fails) implements ForecastStrategy {
        @Override
        public List<Double> forecast(List<Double> context, int horizon) {
            if (fails) {
                throw new IllegalStateException("model is down");
            }
            return values;
        }
    }

    private void stubObservations(int count) {
        List<Observation> newestFirst = new ArrayList<>();
        for (int i = 0; i < count; i++) {
            newestFirst.add(new Observation(NEWEST.minus(STEP.multipliedBy(i)),
                    Observation.ObservationType.KP_INDEX, 1.0 + i, "GFZ"));
        }
        when(observationRepository.findByTypeOrderByTimestampDesc(
                eq(Observation.ObservationType.KP_INDEX), any(Pageable.class))).thenReturn(newestFirst);
    }

    private ForecastService serviceWith(ForecastStrategy... strategies) {
        return new ForecastService(observationRepository, predictionRepository, predictionService,
                eventPublisher, List.of(strategies), HORIZON, CONTEXT);
    }

    @Test
    void savesForecastsForEveryPendingModel() {
        stubObservations(CONTEXT);
        when(predictionRepository.findLatestBaseTime(anyString())).thenReturn(Optional.empty());

        int saved = serviceWith(new PersistenceStrategy(),
                new FakeStrategy("fake", List.of(5.0, 6.0), false)).runIfNeeded();

        assertThat(saved).isEqualTo(4);
        verify(predictionService).replaceBatch(predictionsCaptor.capture());
        List<Prediction> predictions = predictionsCaptor.getValue();
        assertThat(predictions).hasSize(4);
        Prediction first = predictions.stream()
                .filter(p -> p.getModelName().equals("persistence") && p.getStep() == 1)
                .findFirst().orElseThrow();
        assertThat(first.getBaseTime()).isEqualTo(NEWEST);
        assertThat(first.getTargetTime()).isEqualTo(NEWEST.plus(STEP));
        assertThat(first.getPredictedValue()).isEqualTo(1.0);   // найновіше значення в контексті
        verify(eventPublisher).publish(any(ForecastCreatedEvent.class));
    }

    @Test
    void skipsModelsThatAlreadyHaveAForecastForThisBaseTime() {
        stubObservations(CONTEXT);
        when(predictionRepository.findLatestBaseTime("persistence")).thenReturn(Optional.of(NEWEST));
        when(predictionRepository.findLatestBaseTime("fake")).thenReturn(Optional.empty());

        int saved = serviceWith(new PersistenceStrategy(),
                new FakeStrategy("fake", List.of(5.0, 6.0), false)).runIfNeeded();

        assertThat(saved).isEqualTo(2);
        verify(predictionService).replaceBatch(predictionsCaptor.capture());
        assertThat(predictionsCaptor.getValue()).extracting(Prediction::getModelName).containsOnly("fake");
    }

    @Test
    void keepsWorkingWhenOneModelFails() {
        stubObservations(CONTEXT);
        when(predictionRepository.findLatestBaseTime(anyString())).thenReturn(Optional.empty());

        int saved = serviceWith(new PersistenceStrategy(),
                new FakeStrategy("broken", List.of(), true)).runIfNeeded();

        assertThat(saved).isEqualTo(2);
        verify(eventPublisher).publish(eventCaptor.capture());
        assertThat(eventCaptor.getValue().models()).containsExactly("persistence");
    }

    @Test
    void doesNothingWithoutEnoughContext() {
        stubObservations(2);

        int saved = serviceWith(new PersistenceStrategy()).runIfNeeded();

        assertThat(saved).isZero();
        verifyNoInteractions(predictionService, eventPublisher);
    }
}