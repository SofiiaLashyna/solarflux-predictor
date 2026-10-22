package com.sofiia.solarflux.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "predictions")
public class Prediction {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Instant timestamp;

    @Column(nullable = false)
    private Instant targetTime;

    @Column(nullable = false)
    private Double probability;

    private String modelName;

    protected Prediction() {
    }

    public Prediction(Instant timestamp, Instant targetTime, Double probability, String modelName) {
        this.timestamp = timestamp;
        this.targetTime = targetTime;
        this.probability = probability;
        this.modelName = modelName;
    }

    public Long getId() {
        return id;
    }

    public Instant getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Instant timestamp) {
        this.timestamp = timestamp;
    }

    public Instant getTargetTime() {
        return targetTime;
    }

    public void setTargetTime(Instant targetTime) {
        this.targetTime = targetTime;
    }

    public Double getProbability() {
        return probability;
    }

    public void setProbability(Double probability) {
        this.probability = probability;
    }

    public String getModelName() {
        return modelName;
    }

    public void setModelName(String modelName) {
        this.modelName = modelName;
    }
}