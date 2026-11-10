package com.sofiia.solarflux.repository;

import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;

@Repository
public class AccuracyJdbcRepository {

    private static final String SQL = """
            WITH common AS (
                SELECT base_time, target_time
                FROM predictions
                GROUP BY base_time, target_time
                HAVING COUNT(DISTINCT model_name) = (SELECT COUNT(DISTINCT model_name) FROM predictions)
            )
            SELECT p.model_name,
                   ROUND(AVG(ABS(p.predicted_value - o.value))::numeric, 3) AS mae,
                   COUNT(*) AS n
            FROM predictions p
            JOIN common c ON c.base_time = p.base_time AND c.target_time = p.target_time
            JOIN observations o ON o.timestamp = p.target_time AND o.type = 'KP_INDEX'
            GROUP BY p.model_name
            ORDER BY mae
            """;

    private final JdbcTemplate jdbc;

    private static final String BY_STEP_SQL = """
            WITH common AS (
                SELECT base_time, target_time
                FROM predictions
                GROUP BY base_time, target_time
                HAVING COUNT(DISTINCT model_name) = (SELECT COUNT(DISTINCT model_name) FROM predictions)
            )
            SELECT p.model_name, p.step,
                   ROUND(AVG(ABS(p.predicted_value - o.value))::numeric, 3) AS mae,
                   COUNT(*) AS n
            FROM predictions p
            JOIN common c ON c.base_time = p.base_time AND c.target_time = p.target_time
            JOIN observations o ON o.timestamp = p.target_time AND o.type = 'KP_INDEX'
            GROUP BY p.model_name, p.step
            ORDER BY p.step, mae
            """;

    public List<Map<String, Object>> accuracyByStep() {
        return jdbc.queryForList(BY_STEP_SQL);
    }

    public AccuracyJdbcRepository(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public List<Map<String, Object>> accuracyByModel() {
        return jdbc.queryForList(SQL);
    }
}