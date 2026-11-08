package com.sofiia.solarflux.repository;

import com.sofiia.solarflux.model.Prediction;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

@Repository
public interface PredictionRepository extends JpaRepository<Prediction, Long> {

    @Modifying
    @Query("delete from Prediction p where p.modelName = :model and p.baseTime = :baseTime")
    void deleteBatch(@Param("model") String model, @Param("baseTime") Instant baseTime);

    @Query("select max(p.baseTime) from Prediction p where p.modelName = :model")
    Optional<Instant> findLatestBaseTime(@Param("model") String model);

    List<Prediction> findByModelNameAndBaseTimeOrderByTargetTimeAsc(String modelName, Instant baseTime);

    List<Prediction> findByModelNameAndStepOrderByTargetTimeDesc(String modelName, Integer step, Pageable pageable);
}