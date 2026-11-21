package com.sofiia.solarflux.config;

import com.sofiia.solarflux.web.ApiKeyFilter;
import com.sofiia.solarflux.web.HealthServlet;
import com.sofiia.solarflux.web.RequestLoggingFilter;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.boot.web.servlet.ServletRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class WebFilterConfig {

    @Bean
    public FilterRegistrationBean<RequestLoggingFilter> requestLoggingFilter() {
        FilterRegistrationBean<RequestLoggingFilter> bean = new FilterRegistrationBean<>(new RequestLoggingFilter());
        bean.addUrlPatterns("/*");
        bean.setOrder(1);
        return bean;
    }

    @Bean
    public FilterRegistrationBean<ApiKeyFilter> apiKeyFilter(@Value("${security.api-key}") String apiKey) {
        FilterRegistrationBean<ApiKeyFilter> bean = new FilterRegistrationBean<>(new ApiKeyFilter(apiKey));
        bean.addUrlPatterns("/api/*");
        bean.setOrder(2);
        return bean;
    }

    @Bean
    public ServletRegistrationBean<HealthServlet> healthServlet() {
        return new ServletRegistrationBean<>(new HealthServlet(), "/health");
    }
}