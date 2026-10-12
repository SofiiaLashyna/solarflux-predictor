package com.sofiia.solarflux.controller;

import com.sofiia.solarflux.model.Observation;
import com.sofiia.solarflux.service.ObservationService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/observations")
public class ObservationController {

    private final ObservationService observationService;

    public ObservationController(ObservationService observationService) {
        this.observationService = observationService;
    }

    @GetMapping
    public List<Observation> getAllObservations(
            @RequestParam(required = false) Observation.ObservationType type) {
        if (type != null) {
            return observationService.getObservationsByType(type);
        }
        return observationService.getAllObservations();
    }

    @PostMapping
    public ResponseEntity<Observation> createObservation(@RequestBody Observation observation) {
        Observation savedObservation = observationService.saveObservation(observation);
        return new ResponseEntity<>(savedObservation, HttpStatus.CREATED);
    }

    @PostMapping("/batch")
    public ResponseEntity<Integer> createBatch(@RequestBody List<Observation> observations) {
        List<Observation> saved = observationService.saveAll(observations);
        return new ResponseEntity<>(saved.size(), HttpStatus.CREATED);
    }
}