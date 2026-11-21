package com.sofiia.solarflux.service;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.sofiia.solarflux.model.FlareForecast;
import com.sofiia.solarflux.repository.FlareForecastRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class FlareForecastService {

    private static final Logger log = LoggerFactory.getLogger(FlareForecastService.class);

    @JsonIgnoreProperties(ignoreUnknown = true)
    record Noaa(String date, @JsonProperty("m_class_1_day") Integer mClass1Day) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record FlareResponse(@JsonProperty("target_day") String targetDay, double probability,
                         Map<String, Double> features, Noaa noaa,
                         @JsonProperty("recent_m_days") Map<String, Integer> recentMDays) {
    }

    private final FlareForecastRepository repository;
    private final RestClient restClient;
    private final ReentrantLock lock = new ReentrantLock();

    public FlareForecastService(FlareForecastRepository repository,
                                @Value("${forecast.service-url}") String serviceUrl) {
        this.repository = repository;
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(120_000);
        this.restClient = RestClient.builder().baseUrl(serviceUrl).requestFactory(factory).build();
    }

    @Scheduled(initialDelay = 45_000, fixedDelay = 6 * 3_600_000L)
    public void scheduledRun() {
        try {
            fetchAndStore();
        } catch (Exception e) {
            log.warn("Прогноз спалахів не отримано (ML-сервіс запущений?): {}", e.getMessage());
        }
    }

    public FlareForecast fetchAndStore() {
        lock.lock();
        try {
            FlareResponse r = restClient.get().uri("/flare/forecast").retrieve().body(FlareResponse.class);
            if (r == null || r.targetDay() == null) {
                throw new IllegalStateException("ML-сервіс повернув порожню відповідь");
            }
            LocalDate target = LocalDate.parse(r.targetDay());
            FlareForecast forecast = repository.findByTargetDay(target).orElseGet(FlareForecast::new);
            forecast.setTargetDay(target);
            forecast.setProbability(r.probability());
            if (r.noaa() != null && r.noaa().mClass1Day() != null && r.noaa().date() != null) {
                forecast.setNoaaMProbability(r.noaa().mClass1Day());
                forecast.setNoaaDate(LocalDate.parse(r.noaa().date()));
            }
            forecast = repository.save(forecast);

            if (r.recentMDays() != null) {
                for (FlareForecast f : repository.findByActualIsNull()) {
                    Integer flag = r.recentMDays().get(f.getTargetDay().toString());
                    if (flag != null && f.getTargetDay().isBefore(target)) {
                        f.setActual(flag > 0);
                        repository.save(f);
                    }
                }
            }
            log.info("Прогноз спалахів на {}: {}%", target, Math.round(r.probability() * 100));
            return forecast;
        } finally {
            lock.unlock();
        }
    }
}