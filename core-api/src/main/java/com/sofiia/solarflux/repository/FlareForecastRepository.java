package com.sofiia.solarflux.repository;

import com.sofiia.solarflux.model.FlareForecast;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

@Repository
public interface FlareForecastRepository extends JpaRepository<FlareForecast, Long> {

    Optional<FlareForecast> findByTargetDay(LocalDate targetDay);

    List<FlareForecast> findAllByOrderByTargetDayDesc(Pageable pageable);
}