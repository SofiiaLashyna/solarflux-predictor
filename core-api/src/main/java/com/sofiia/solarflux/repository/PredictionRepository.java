package com.sofiia.solarflux.repository;

import com.sofiia.solarflux.model.Prediction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PredictionRepository extends JpaRepository<Prediction, Long> {
    List<Prediction> findAllByOrderByTimestampDesc();
}