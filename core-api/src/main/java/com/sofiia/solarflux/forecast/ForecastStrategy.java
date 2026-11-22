package com.sofiia.solarflux.forecast;

import java.util.List;

public interface ForecastStrategy {

    String modelName();

    List<Double> forecast(List<Double> context, int horizon);
}