package com.sofiia.solarflux.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "observations")
public class Observation {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Instant timestamp;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ObservationType type;

    @Column(nullable = false)
    private Double value;

    private String source;

    protected Observation() {

    }

    public Observation(Instant timestamp, ObservationType type, Double value, String source) {
        this.timestamp = timestamp;
        this.type = type;
        this.value = value;
        this.source = source;
    }

    public Long getId() {
        return id;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public ObservationType getType() {
        return type;
    }

    public Double getValue() {
        return value;
    }

    public String getSource() {
        return source;
    }

    public enum ObservationType {
        KP_INDEX,
        XRAY_FLUX
    }
}