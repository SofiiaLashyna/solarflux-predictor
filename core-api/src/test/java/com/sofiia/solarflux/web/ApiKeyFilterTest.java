package com.sofiia.solarflux.web;

import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockFilterChain;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;

import static org.assertj.core.api.Assertions.assertThat;

class ApiKeyFilterTest {

    private final ApiKeyFilter filter = new ApiKeyFilter("secret");

    @Test
    void rejectsWriteRequestWithoutKey() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("POST", "/api/sync");
        MockHttpServletResponse res = new MockHttpServletResponse();
        MockFilterChain chain = new MockFilterChain();

        filter.doFilter(req, res, chain);

        assertThat(res.getStatus()).isEqualTo(401);
        assertThat(chain.getRequest()).isNull();
    }

    @Test
    void rejectsWriteRequestWithWrongKey() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("POST", "/api/sync");
        req.addHeader("X-API-Key", "wrong");
        MockHttpServletResponse res = new MockHttpServletResponse();
        MockFilterChain chain = new MockFilterChain();

        filter.doFilter(req, res, chain);

        assertThat(res.getStatus()).isEqualTo(401);
        assertThat(chain.getRequest()).isNull();
    }

    @Test
    void allowsWriteRequestWithCorrectKey() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("POST", "/api/sync");
        req.addHeader("X-API-Key", "secret");
        MockHttpServletResponse res = new MockHttpServletResponse();
        MockFilterChain chain = new MockFilterChain();

        filter.doFilter(req, res, chain);

        assertThat(res.getStatus()).isEqualTo(200);
        assertThat(chain.getRequest()).isNotNull();
    }

    @Test
    void allowsReadRequestWithoutKey() throws Exception {
        MockHttpServletRequest req = new MockHttpServletRequest("GET", "/api/observations/latest");
        MockHttpServletResponse res = new MockHttpServletResponse();
        MockFilterChain chain = new MockFilterChain();

        filter.doFilter(req, res, chain);

        assertThat(chain.getRequest()).isNotNull();
    }
}