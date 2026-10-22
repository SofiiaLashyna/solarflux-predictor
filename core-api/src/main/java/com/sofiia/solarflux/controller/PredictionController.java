package com.sofiia.solarflux.controller;

import com.sofiia.solarflux.model.Prediction;
import com.sofiia.solarflux.service.PredictionService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/predictions")
public class PredictionController {

    private final PredictionService predictionService;

    public PredictionController(PredictionService predictionService) {
        this.predictionService = predictionService;
    }

    @GetMapping
    public List<Prediction> getAllPredictions() {
        return predictionService.getAllPredictions();
    }

    @PostMapping
    public ResponseEntity<Prediction> createPrediction(@RequestBody Prediction prediction) {
        Prediction savedPrediction = predictionService.savePrediction(prediction);
        return new ResponseEntity<>(savedPrediction, HttpStatus.CREATED);
    }
}