package com.sofiia.solarflux.controller;

import com.sofiia.solarflux.service.ForecastService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/forecast")
public class ForecastController {

    private final ForecastService forecastService;

    public ForecastController(ForecastService forecastService) {
        this.forecastService = forecastService;
    }

    @PostMapping("/run")
    public Map<String, Integer> run() {
        return Map.of("saved", forecastService.runIfNeeded());
    }
}