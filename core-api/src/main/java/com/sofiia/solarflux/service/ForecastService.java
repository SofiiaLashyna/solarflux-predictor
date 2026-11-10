package com.sofiia.solarflux.service;

import com.sofiia.solarflux.model.Observation;
import com.sofiia.solarflux.model.Prediction;
import com.sofiia.solarflux.repository.ObservationRepository;
import com.sofiia.solarflux.repository.PredictionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class ForecastService {

    private static final Logger log = LoggerFactory.getLogger(ForecastService.class);
    private static final Duration STEP = Duration.ofHours(3);

    record ForecastRequest(List<Double> context, int horizon, List<String> models) {
    }

    record ForecastResponse(Map<String, List<Double>> forecasts) {
    }

    private final ObservationRepository observationRepository;
    private final PredictionRepository predictionRepository;
    private final PredictionService predictionService;
    private final RestClient restClient;
    private final List<String> models;
    private final int horizon;
    private final int contextLength;
    private final ReentrantLock lock = new ReentrantLock();

    public ForecastService(ObservationRepository observationRepository,
                           PredictionRepository predictionRepository,
                           PredictionService predictionService,
                           @Value("${forecast.service-url}") String serviceUrl,
                           @Value("${forecast.models}") List<String> models,
                           @Value("${forecast.horizon}") int horizon,
                           @Value("${forecast.context-length}") int contextLength) {
        this.observationRepository = observationRepository;
        this.predictionRepository = predictionRepository;
        this.predictionService = predictionService;
        this.models = models;
        this.horizon = horizon;
        this.contextLength = contextLength;

        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(120_000);
        this.restClient = RestClient.builder().baseUrl(serviceUrl).requestFactory(factory).build();
    }

    @Scheduled(initialDelay = 30_000, fixedDelay = 600_000)
    public void scheduledRun() {
        try {
            runIfNeeded();
        } catch (Exception e) {
            log.warn("Автопрогноз не виконано (ML-сервіс запущений?): {}", e.getMessage());
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

            List<String> pending = models.stream()
                    .filter(m -> predictionRepository.findLatestBaseTime(m).map(b -> !b.equals(base)).orElse(true))
                    .toList();
            if (pending.isEmpty()) {
                log.debug("Прогнози від {} уже є", base);
                return 0;
            }

            List<Double> context = latest.stream().map(Observation::getValue).toList();
            ForecastResponse response = restClient.post()
                    .uri("/forecast")
                    .body(new ForecastRequest(context, horizon, pending))
                    .retrieve()
                    .body(ForecastResponse.class);
            if (response == null || response.forecasts() == null) {
                throw new IllegalStateException("ML-сервіс повернув порожню відповідь");
            }

            List<Prediction> predictions = new ArrayList<>();
            for (Map.Entry<String, List<Double>> entry : response.forecasts().entrySet()) {
                List<Double> values = entry.getValue();
                for (int step = 1; step <= values.size(); step++) {
                    predictions.add(new Prediction(entry.getKey(), base,
                            base.plus(STEP.multipliedBy(step)), step, values.get(step - 1)));
                }
            }
            predictionService.replaceBatch(predictions);
            log.info("Автопрогноз від {}: збережено {} прогнозів для {}", base, predictions.size(), pending);
            return predictions.size();
        } finally {
            lock.unlock();
        }
    }
}