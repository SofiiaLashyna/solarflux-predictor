package com.sofiia.solarflux.service;

import com.sofiia.solarflux.model.Prediction;
import com.sofiia.solarflux.repository.PredictionRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

@Service
public class PredictionService {

    private record Key(String model, Instant baseTime) {
    }

    private final PredictionRepository predictionRepository;

    public PredictionService(PredictionRepository predictionRepository) {
        this.predictionRepository = predictionRepository;
    }

    @Transactional
    public List<Prediction> replaceBatch(List<Prediction> predictions) {
        predictions.stream()
                .map(p -> new Key(p.getModelName(), p.getBaseTime()))
                .distinct()
                .forEach(k -> predictionRepository.deleteBatch(k.model(), k.baseTime()));
        return predictionRepository.saveAll(predictions);
    }

    @Transactional(readOnly = true)
    public List<Prediction> getLatest(String model) {
        return predictionRepository.findLatestBaseTime(model)
                .map(base -> predictionRepository.findByModelNameAndBaseTimeOrderByTargetTimeAsc(model, base))
                .orElse(List.of());
    }

    @Transactional(readOnly = true)
    public List<Prediction> getHistory(String model, int step, int limit) {
        return predictionRepository.findByModelNameAndStepOrderByTargetTimeDesc(model, step, PageRequest.of(0, limit));
    }

    @Transactional(readOnly = true)
    public List<Instant> getBaseTimes(String model, int limit) {
        return predictionRepository.findBaseTimes(model, PageRequest.of(0, limit));
    }

    @Transactional(readOnly = true)
    public List<Prediction> getBatch(String model, Instant baseTime) {
        return predictionRepository.findByModelNameAndBaseTimeOrderByTargetTimeAsc(model, baseTime);
    }
}