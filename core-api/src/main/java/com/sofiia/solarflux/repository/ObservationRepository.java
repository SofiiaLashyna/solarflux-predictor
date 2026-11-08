package com.sofiia.solarflux.repository;

import com.sofiia.solarflux.model.Observation;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ObservationRepository extends JpaRepository<Observation, Long> {

    List<Observation> findByTypeOrderByTimestampDesc(Observation.ObservationType type);

    List<Observation> findByTypeOrderByTimestampDesc(Observation.ObservationType type, Pageable pageable);
}