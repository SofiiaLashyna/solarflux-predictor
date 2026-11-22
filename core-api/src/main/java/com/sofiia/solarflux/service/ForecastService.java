package com.sofiia.solarflux.service;

import com.sofiia.solarflux.forecast.ForecastStrategy;
import com.sofiia.solarflux.forecast.ForecastStrategyFactory;
import com.sofiia.solarflux.forecast.ForecastBatch;
import com.sofiia.solarflux.forecast.ForecastObserver;
import com.sofiia.solarflux.model.Observation;
import com.sofiia.solarflux.model.Prediction;
import com.sofiia.solarflux.repository.ObservationRepository;
import com.sofiia.solarflux.repository.PredictionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class ForecastService {

    private static final Logger log = LoggerFactory.getLogger(ForecastService.class);
    private static final Duration STEP = Duration.ofHours(3);

    private final ObservationRepository observationRepository;
    private final PredictionRepository predictionRepository;
    private final PredictionService predictionService;
    private final List<ForecastObserver> observers;
    private final List<ForecastStrategy> strategies;
    private final int horizon;
    private final int contextLength;
    private final ReentrantLock lock = new ReentrantLock();

    @Autowired
    public ForecastService(ObservationRepository observationRepository,
                           PredictionRepository predictionRepository,
                           PredictionService predictionService,
                           List<ForecastObserver> observers,
                           ForecastStrategyFactory factory,
                           @Value("${forecast.models}") List<String> models,
                           @Value("${forecast.horizon}") int horizon,
                           @Value("${forecast.context-length}") int contextLength) {
        this(observationRepository, predictionRepository, predictionService, observers,
                models.stream().map(factory::create).toList(), horizon, contextLength);
    }

    ForecastService(ObservationRepository observationRepository,
                    PredictionRepository predictionRepository,
                    PredictionService predictionService,
                    List<ForecastObserver> observers,
                    List<ForecastStrategy> strategies,
                    int horizon,
                    int contextLength) {
        this.observationRepository = observationRepository;
        this.predictionRepository = predictionRepository;
        this.predictionService = predictionService;
        this.observers = observers;
        this.strategies = strategies;
        this.horizon = horizon;
        this.contextLength = contextLength;
    }

    @Scheduled(initialDelay = 30_000, fixedDelay = 600_000)
    public void scheduledRun() {
        try {
            runIfNeeded();
        } catch (Exception e) {
            log.warn("Автопрогноз не виконано: {}", e.getMessage());
        }
    }

    private void notifyObservers(ForecastBatch batch) {
        for (ForecastObserver observer : observers) {
            try {
                observer.onForecastsStored(batch);
            } catch (Exception e) {
                log.warn("Спостерігач {} не впорався: {}", observer.getClass().getSimpleName(), e.getMessage());
            }
        }
    }

    public int runIfNeeded() {
        if (!lock.tryLock()) {
            return 0;
        }
        try {
            List<Observation> latest = new ArrayList<>(observationRepository.findByTypeOrderByTimestampDesc(
                    Observation.ObservationType.KP_INDEX, PageRequest.of(0, contextLength)));
            if (latest.size() < contextLength) {
                log.warn("Недостатньо даних для контексту: {} з {}", latest.size(), contextLength);
                return 0;
            }
            Collections.reverse(latest);   // від старих до нових
            Instant base = latest.get(latest.size() - 1).getTimestamp();

            List<ForecastStrategy> pending = strategies.stream()
                    .filter(s -> predictionRepository.findLatestBaseTime(s.modelName())
                            .map(b -> !b.equals(base)).orElse(true))
                    .toList();
            if (pending.isEmpty()) {
                log.debug("Прогнози від {} уже є", base);
                return 0;
            }

            List<Double> context = latest.stream().map(Observation::getValue).toList();
            List<Prediction> predictions = new ArrayList<>();
            List<String> done = new ArrayList<>();
            for (ForecastStrategy strategy : pending) {
                try {
                    List<Double> values = strategy.forecast(context, horizon);
                    for (int step = 1; step <= values.size(); step++) {
                        predictions.add(new Prediction(strategy.modelName(), base,
                                base.plus(STEP.multipliedBy(step)), step, values.get(step - 1)));
                    }
                    done.add(strategy.modelName());
                } catch (Exception e) {
                    log.warn("Модель {} не дала прогнозу: {}", strategy.modelName(), e.getMessage());
                }
            }
            if (predictions.isEmpty()) {
                return 0;
            }
            predictionService.replaceBatch(predictions);
            notifyObservers(new ForecastBatch(base, predictions));
            log.info("Автопрогноз від {}: збережено {} прогнозів для {}", base, predictions.size(), done);
            return predictions.size();
        } finally {
            lock.unlock();
        }
    }
}