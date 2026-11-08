package com.sofiia.solarflux.model;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "predictions", uniqueConstraints =
@UniqueConstraint(name = "uq_prediction", columnNames = {"model_name", "base_time", "target_time"}))
public class Prediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "model_name", nullable = false)
    private String modelName;

    @Column(name = "base_time", nullable = false)
    private Instant baseTime;

    @Column(name = "target_time", nullable = false)
    private Instant targetTime;

    @Column(nullable = false)
    private Integer step;

    @Column(name = "predicted_value", nullable = false)
    private Double predictedValue;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    protected Prediction() {
    }

    public Prediction(String modelName, Instant baseTime, Instant targetTime, Integer step, Double predictedValue) {
        this.modelName = modelName;
        this.baseTime = baseTime;
        this.targetTime = targetTime;
        this.step = step;
        this.predictedValue = predictedValue;
    }

    public Long getId() { return id; }
    public String getModelName() { return modelName; }
    public Instant getBaseTime() { return baseTime; }
    public Instant getTargetTime() { return targetTime; }
    public Integer getStep() { return step; }
    public Double getPredictedValue() { return predictedValue; }
    public Instant getCreatedAt() { return createdAt; }
}