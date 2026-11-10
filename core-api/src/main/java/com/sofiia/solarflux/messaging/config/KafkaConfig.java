package com.sofiia.solarflux.config;

import com.sofiia.solarflux.messaging.ForecastEventPublisher;
import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.TopicBuilder;

@Configuration
public class KafkaConfig {

    @Bean
    public NewTopic forecastCreatedTopic() {
        return TopicBuilder.name(ForecastEventPublisher.TOPIC).partitions(1).replicas(1).build();
    }
}