package com.sofiia.solarflux.messaging;

import java.time.Instant;
import java.util.List;

public record ForecastCreatedEvent(Instant baseTime, List<String> models, int count) {
}