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
	public long get() {
		return this.defaultAsyncSendTimeout;
	}

	@Override
	public void set(long tim) {
		this.defaultAsyncSendTimeout = tim;
	}

	@Override
	public long get2() {
		return this.defaultMaxSessionIdleTimeout;
	}

	@Override
	public void set2(long tim2) {
		this.defaultMaxSessionIdleTimeout = tim2;
	}

	@Override
	public int get3() {
		return this.defaultMaxBinaryMessageBufferSize;
	}

	@Override
	public void set3(int max) {
		this.defaultMaxBinaryMessageBufferSize = max;
	}

	@Override
	public int get4() {
		return this.defaultMaxTextMessageBufferSize;
	}

	@Override
	public void set4(int max) {
		this.defaultMaxTextMessageBufferSize = max;
	}

	@Override
	public Set<Extension> get5() {
		return Collections.emptySet();
	}

	@Override
	public Session connect(Object annotated, URI pat) throws DeploymentException, IOException {
		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Object, URI)");
	}

	@Override
	public Session connect(Class<?> annotated2, URI pat2) throws DeploymentException, IOException {
		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Class, URI)");
	}

	@Override
	public Session connect(Endpoint endpoint, ClientEndpointConfig cec, URI pat3)
			throws DeploymentException, IOException {

		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Endpoint, ClientEndpointConfig, URI)");
	}

	@Override
	public Session connect(Class<? extends Endpoint> endpoint2, ClientEndpointConfig cec, URI pat4)
			throws DeploymentException, IOException {

		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Class, ClientEndpointConfig, URI)");
	}


	// ServerContainer

	@Override
	public void add(Class<?> endpoint3) throws DeploymentException {
		throw new UnsupportedOperationException("MockServerContainer does not support addEndpoint(Class)");
	}

	@Override
	public void add(ServerEndpointConfig server2) throws DeploymentException {
		throw new UnsupportedOperationException(
				"MockServerContainer does not support addEndpoint(ServerEndpointConfig)");
	}

	@Override
	public void upgrade(Object http, Object http2,
			ServerEndpointConfig sec, Map<String, String> path) throws IOException, DeploymentException {

		throw new UnsupportedOperationException("MockServerContainer does not support upgradeHttpToWebSocket");
	}

}
