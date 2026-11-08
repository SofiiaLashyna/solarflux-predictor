package com.sofiia.solarflux.service;

import com.sofiia.solarflux.model.Observation;
import com.sofiia.solarflux.repository.ObservationRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.data.domain.PageRequest;

import java.util.List;

@Service
public class ObservationService {

    private final ObservationRepository observationRepository;

    public ObservationService(ObservationRepository observationRepository) {
        this.observationRepository = observationRepository;
    }

    public List<Observation> getAllObservations() {
        return observationRepository.findAll();
    }

    public List<Observation> getObservationsByType(Observation.ObservationType type) {
        return observationRepository.findByTypeOrderByTimestampDesc(type);
    }

    public List<Observation> getLatest(Observation.ObservationType type, int limit) {
        return observationRepository.findByTypeOrderByTimestampDesc(type, PageRequest.of(0, limit));
    }

    @Transactional
    public Observation saveObservation(Observation observation) {
        return observationRepository.save(observation);
    }

    @Transactional
    public List<Observation> saveAll(List<Observation> observations) {
        return observationRepository.saveAll(observations);
    }
}