package com.sofiia.solarflux.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "flare_forecasts", uniqueConstraints =
@UniqueConstraint(name = "uq_flare_forecast_day", columnNames = "target_day"))
public class FlareForecast {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "target_day", nullable = false)
    private LocalDate targetDay;

    @Column(nullable = false)
    private Double probability;

    @Column(name = "noaa_m_probability")
    private Integer noaaMProbability;

    @Column(name = "noaa_date")
    private LocalDate noaaDate;

    private Boolean actual;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    public Long getId() { return id; }
    public LocalDate getTargetDay() { return targetDay; }
    public void setTargetDay(LocalDate targetDay) { this.targetDay = targetDay; }
    public Double getProbability() { return probability; }
    public void setProbability(Double probability) { this.probability = probability; }
    public Integer getNoaaMProbability() { return noaaMProbability; }
    public void setNoaaMProbability(Integer noaaMProbability) { this.noaaMProbability = noaaMProbability; }
    public LocalDate getNoaaDate() { return noaaDate; }
    public void setNoaaDate(LocalDate noaaDate) { this.noaaDate = noaaDate; }
    public Boolean getActual() { return actual; }
    public void setActual(Boolean actual) { this.actual = actual; }
    public Instant getCreatedAt() { return createdAt; }
}