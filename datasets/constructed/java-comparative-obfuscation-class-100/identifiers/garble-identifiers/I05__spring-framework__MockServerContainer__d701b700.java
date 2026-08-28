package org.springframework.test.context.web.socket;
import java.io.IOException;
import java.net.URI;
import java.util.Collections;
import java.util.Map;
import java.util.Set;
import jakarta.websocket.ClientEndpointConfig;
import jakarta.websocket.DeploymentException;
import jakarta.websocket.Endpoint;
import jakarta.websocket.Extension;
import jakarta.websocket.Session;
import jakarta.websocket.server.ServerContainer;
import jakarta.websocket.server.ServerEndpointConfig;

/**
 * Mock implementation of the {@link jakarta.websocket.server.ServerContainer} interface.
 *
 * @author Sam Brannen
 * @since 4.3.1
 */
class MockServerContainer implements ServerContainer {

	private long defaultAsyncSendTimeout;

	private long defaultMaxSessionIdleTimeout;

	private int defaultMaxBinaryMessageBufferSize;

	private int defaultMaxTextMessageBufferSize;


	// WebSocketContainer

	@Override
	public long a() {
		return this.defaultAsyncSendTimeout;
	}

	@Override
	public void b(long a) {
		this.defaultAsyncSendTimeout = a;
	}

	@Override
	public long c() {
		return this.defaultMaxSessionIdleTimeout;
	}

	@Override
	public void d(long b) {
		this.defaultMaxSessionIdleTimeout = b;
	}

	@Override
	public int e() {
		return this.defaultMaxBinaryMessageBufferSize;
	}

	@Override
	public void f(int c) {
		this.defaultMaxBinaryMessageBufferSize = c;
	}

	@Override
	public int g() {
		return this.defaultMaxTextMessageBufferSize;
	}

	@Override
	public void h(int d) {
		this.defaultMaxTextMessageBufferSize = d;
	}

	@Override
	public Set<Extension> i() {
		return Collections.emptySet();
	}

	@Override
	public Session j(Object e, URI f) throws DeploymentException, IOException {
		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Object, URI)");
	}

	@Override
	public Session j(Class<?> g, URI h) throws DeploymentException, IOException {
		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Class, URI)");
	}

	@Override
	public Session j(Endpoint i, ClientEndpointConfig j, URI k)
			throws DeploymentException, IOException {

		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Endpoint, ClientEndpointConfig, URI)");
	}

	@Override
	public Session j(Class<? extends Endpoint> l, ClientEndpointConfig m, URI n)
			throws DeploymentException, IOException {

		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Class, ClientEndpointConfig, URI)");
	}


	// ServerContainer

	@Override
	public void k(Class<?> o) throws DeploymentException {
		throw new UnsupportedOperationException("MockServerContainer does not support addEndpoint(Class)");
	}

	@Override
	public void k(ServerEndpointConfig p) throws DeploymentException {
		throw new UnsupportedOperationException(
				"MockServerContainer does not support addEndpoint(ServerEndpointConfig)");
	}

	@Override
	public void l(Object q, Object r,
			ServerEndpointConfig s, Map<String, String> t) throws IOException, DeploymentException {

		throw new UnsupportedOperationException("MockServerContainer does not support upgradeHttpToWebSocket");
	}

}
