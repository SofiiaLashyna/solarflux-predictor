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

    @PostMapping("/batch")
    public ResponseEntity<Integer> createBatch(@RequestBody List<Prediction> predictions) {
        return new ResponseEntity<>(predictionService.replaceBatch(predictions).size(), HttpStatus.CREATED);
    }

    @GetMapping("/latest")
    public List<Prediction> getLatest(@RequestParam String model) {
        return predictionService.getLatest(model);
    }

    @GetMapping
    public List<Prediction> getHistory(
            @RequestParam String model,
            @RequestParam(defaultValue = "1") int step,
            @RequestParam(defaultValue = "240") int limit) {
        return predictionService.getHistory(model, step, Math.min(limit, 2000));
    }
}