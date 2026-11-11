package com.sofiia.solarflux.messaging;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class ForecastEventListener {

    private static final Logger log = LoggerFactory.getLogger(ForecastEventListener.class);

    private final ForecastWebSocketHandler webSocketHandler;

    public ForecastEventListener(ForecastWebSocketHandler webSocketHandler) {
        this.webSocketHandler = webSocketHandler;
    }

    @KafkaListener(topics = ForecastEventPublisher.TOPIC)
    public void onForecastCreated(String payload) {
        log.info("Отримано подію з Kafka: {}", payload);
        webSocketHandler.broadcast("{\"type\":\"forecast.created\",\"data\":" + payload + "}");
    }
}