package com.sofiia.solarflux.controller;

import com.sofiia.solarflux.model.FlareForecast;
import com.sofiia.solarflux.repository.FlareForecastRepository;
import com.sofiia.solarflux.service.FlareForecastService;
import org.springframework.data.domain.PageRequest;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/flares")
public class FlareController {

    private final FlareForecastService service;
    private final FlareForecastRepository repository;

    public FlareController(FlareForecastService service, FlareForecastRepository repository) {
        this.service = service;
        this.repository = repository;
    }

    @GetMapping("/forecast")
    public List<FlareForecast> history(@RequestParam(defaultValue = "30") int limit) {
        return repository.findAllByOrderByTargetDayDesc(PageRequest.of(0, Math.min(limit, 365)));
    }

    @PostMapping("/forecast/run")
    public FlareForecast run() {
        return service.fetchAndStore();
    }
}