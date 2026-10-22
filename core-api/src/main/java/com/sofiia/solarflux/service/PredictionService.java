package com.sofiia.solarflux.service;

import com.sofiia.solarflux.model.Prediction;
import com.sofiia.solarflux.repository.PredictionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional(readOnly = true)
public class PredictionService {

    private final PredictionRepository predictionRepository;

    public PredictionService(PredictionRepository predictionRepository) {
        this.predictionRepository = predictionRepository;
    }

    public List<Prediction> getAllPredictions() {
        return predictionRepository.findAllByOrderByTimestampDesc();
    }

    @Transactional
    public Prediction savePrediction(Prediction prediction) {
        return predictionRepository.save(prediction);
    }
}