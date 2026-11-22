package com.sofiia.solarflux.forecast;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

@Component
public class MlServiceClient {

    record ForecastRequest(List<Double> context, int horizon, List<String> models) {
    }

    record ForecastResponse(Map<String, List<Double>> forecasts) {
    }

    private final RestClient restClient;

    public MlServiceClient(@Value("${forecast.service-url}") String serviceUrl) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);
        factory.setReadTimeout(120_000);
        this.restClient = RestClient.builder().baseUrl(serviceUrl).requestFactory(factory).build();
    }

    public List<Double> forecast(String model, List<Double> context, int horizon) {
        ForecastResponse response = restClient.post()
                .uri("/forecast")
                .body(new ForecastRequest(context, horizon, List.of(model)))
                .retrieve()
                .body(ForecastResponse.class);
        if (response == null || response.forecasts() == null || !response.forecasts().containsKey(model)) {
            throw new IllegalStateException("ML-сервіс не повернув прогноз для " + model);
        }
        return response.forecasts().get(model);
    }
}