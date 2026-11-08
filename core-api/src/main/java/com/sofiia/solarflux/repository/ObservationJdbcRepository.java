package com.sofiia.solarflux.repository;

import com.sofiia.solarflux.model.Observation;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.sql.Timestamp;
import java.time.Instant;
import java.util.List;

@Repository
public class ObservationJdbcRepository {

    private static final String UPSERT = """
            INSERT INTO observations ("timestamp", type, source, value, status)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT ("timestamp", type, source)
            DO UPDATE SET value = EXCLUDED.value, status = EXCLUDED.status
            """;

    private final JdbcTemplate jdbc;

    public ObservationJdbcRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    @Transactional
    public void upsertAll(List<Observation> observations) {
        List<Object[]> rows = observations.stream()
                .map(o -> new Object[]{Timestamp.from(o.getTimestamp()), o.getType().name(),
                        o.getSource(), o.getValue(), o.getStatus()})
                .toList();
        jdbc.batchUpdate(UPSERT, rows);
    }

    public Instant latestTimestamp(boolean definitiveOnly) {
        String sql = "SELECT MAX(\"timestamp\") FROM observations WHERE type = 'KP_INDEX'"
                + (definitiveOnly ? " AND status = 'def'" : "");
        Timestamp ts = jdbc.queryForObject(sql, Timestamp.class);
        return ts == null ? null : ts.toInstant();
    }
}