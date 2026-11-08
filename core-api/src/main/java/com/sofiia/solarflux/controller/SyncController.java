package com.sofiia.solarflux.controller;

import com.sofiia.solarflux.service.ObservationSyncService;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/sync")
public class SyncController {

    private final ObservationSyncService syncService;

    public SyncController(ObservationSyncService syncService) {
        this.syncService = syncService;
    }

    @PostMapping
    public Map<String, Integer> sync() {
        return Map.of("synced", syncService.sync());
    }
}