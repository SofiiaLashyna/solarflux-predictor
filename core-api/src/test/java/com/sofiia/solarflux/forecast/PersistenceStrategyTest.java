package com.sofiia.solarflux.forecast;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class PersistenceStrategyTest {

    private final PersistenceStrategy strategy = new PersistenceStrategy();

    @Test
    void repeatsTheLastObservedValue() {
        assertThat(strategy.forecast(List.of(1.0, 2.5, 3.0), 4)).containsExactly(3.0, 3.0, 3.0, 3.0);
    }

    @Test
    void rejectsAnEmptyContext() {
        assertThatThrownBy(() -> strategy.forecast(List.of(), 3)).isInstanceOf(IllegalArgumentException.class);
    }
}