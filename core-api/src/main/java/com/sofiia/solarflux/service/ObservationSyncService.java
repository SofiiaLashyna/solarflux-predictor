package com.sofiia.solarflux.service;

import com.sofiia.solarflux.client.GfzKpClient;
import com.sofiia.solarflux.model.Observation;
import com.sofiia.solarflux.repository.ObservationJdbcRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class ObservationSyncService {

    private static final Logger log = LoggerFactory.getLogger(ObservationSyncService.class);
    private static final Duration STEP = Duration.ofHours(3);

    private final GfzKpClient gfzClient;
    private final ObservationJdbcRepository jdbcRepository;
    private final ReentrantLock lock = new ReentrantLock();

    public ObservationSyncService(GfzKpClient gfzClient, ObservationJdbcRepository jdbcRepository) {
        this.gfzClient = gfzClient;
        this.jdbcRepository = jdbcRepository;
    }

    @Scheduled(initialDelay = 5_000, fixedDelay = 3_600_000)
    public void scheduledSync() {
        try {
            sync();
        } catch (Exception e) {
            log.error("Синхронізація Kp не вдалася: {}", e.getMessage());
        }
    }

    public int sync() {
        if (!lock.tryLock()) {
            log.info("Синхронізація вже виконується, пропускаю");
            return 0;
        }
        try {
            Instant lastDefinitive = jdbcRepository.latestTimestamp(true);
            Instant last = lastDefinitive != null ? lastDefinitive : jdbcRepository.latestTimestamp(false);
            Instant from = last != null ? last.plus(STEP) : Instant.parse("2021-01-01T00:00:00Z");
            Instant to = Instant.now();
            if (!from.isBefore(to)) {
                log.info("Нових даних немає");
                return 0;
            }
            List<Observation> fresh = gfzClient.fetch(from, to);
            jdbcRepository.upsertAll(fresh);
            log.info("Kp синхронізовано: {} записів ({} - {})", fresh.size(), from, to);
            return fresh.size();
        } finally {
            lock.unlock();
        }
    }
}