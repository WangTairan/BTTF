package org.springframework.test.web.reactive.server;
import org.jspecify.annotations.Nullable;
import org.springframework.http.client.reactive.ClientHttpConnector;
import org.springframework.web.server.adapter.WebHttpHandlerBuilder;










public interface WebTestClientConfigurer {

	









	void afterConfigurerAdded(WebTestClient.Builder builder,
			@Nullable WebHttpHandlerBuilder httpHandlerBuilder,
			@Nullable ClientHttpConnector connector);

}
