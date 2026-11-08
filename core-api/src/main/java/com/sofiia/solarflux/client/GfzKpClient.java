package com.sofiia.solarflux.client;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sofiia.solarflux.model.Observation;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.List;

@Component
public class GfzKpClient {

    private static final String URL = "https://kp.gfz.de/app/json/?start={start}&end={end}&index=Kp";

    private final ObjectMapper objectMapper;
    private final RestClient restClient = RestClient.builder()
            .defaultHeader("User-Agent", "solarflux-predictor/0.1 (student project)")
            .build();

    public GfzKpClient(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record GfzResponse(
            @JsonProperty("Kp") List<Double> kp,
            @JsonProperty("datetime") List<String> datetime,
            @JsonProperty("status") List<String> status) {
    }

    public List<Observation> fetch(Instant from, Instant to) {
        String json = restClient.get()
                .uri(URL, from.truncatedTo(ChronoUnit.SECONDS), to.truncatedTo(ChronoUnit.SECONDS))
                .retrieve()
                .body(String.class);

        GfzResponse response;
        try {
            response = objectMapper.readValue(json, GfzResponse.class);
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Не вдалося розібрати відповідь GFZ", e);
        }

        List<Observation> result = new ArrayList<>();
        if (response.kp() == null) {
            return result;
        }
        for (int i = 0; i < response.kp().size(); i++) {
            double value = response.kp().get(i);
            if (value < 0) {
                continue;
            }
            Observation observation = new Observation(
                    Instant.parse(response.datetime().get(i)),
                    Observation.ObservationType.KP_INDEX,
                    value,
                    "GFZ");
            if (response.status() != null) {
                observation.setStatus(response.status().get(i));
            }
            result.add(observation);
        }
        return result;
    }
}