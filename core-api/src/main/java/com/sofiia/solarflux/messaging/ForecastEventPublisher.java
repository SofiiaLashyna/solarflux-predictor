package com.sofiia.solarflux.messaging;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class ForecastEventPublisher {

    public static final String TOPIC = "forecast.created";
    private static final Logger log = LoggerFactory.getLogger(ForecastEventPublisher.class);

    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    public ForecastEventPublisher(KafkaTemplate<String, String> kafkaTemplate, ObjectMapper objectMapper) {
        this.kafkaTemplate = kafkaTemplate;
        this.objectMapper = objectMapper;
    }

    public void publish(ForecastCreatedEvent event) {
        try {
            kafkaTemplate.send(TOPIC, event.baseTime().toString(), objectMapper.writeValueAsString(event))
                    .whenComplete((result, error) -> {
                        if (error != null) {
                            log.warn("Подію не надіслано в Kafka: {}", error.getMessage());
                        } else {
                            log.info("Подію надіслано: partition={}, offset={}",
                                    result.getRecordMetadata().partition(), result.getRecordMetadata().offset());
                        }
                    });
        } catch (Exception e) {
            log.warn("Не вдалося сформувати подію: {}", e.getMessage());
        }
    }
}