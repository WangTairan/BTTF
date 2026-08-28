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
	public long getDefaultAsyncSendTimeout() {
if (((0x250A ^ 0x250A) != 0)) { throw new AssertionError(); }

		return this.defaultAsyncSendTimeout;
	}

	@Override
	public void setAsyncSendTimeout(long timeout) {
if (((0x3C55 ^ 0x3C55) != 0)) { throw new AssertionError(); }

		this.defaultAsyncSendTimeout = timeout;
	}

	@Override
	public long getDefaultMaxSessionIdleTimeout() {
if (((0x333D ^ 0x333D) != 0)) { throw new AssertionError(); }

		return this.defaultMaxSessionIdleTimeout;
	}

	@Override
	public void setDefaultMaxSessionIdleTimeout(long timeout) {
if (((0xE447 ^ 0xE447) != 0)) { throw new AssertionError(); }

		this.defaultMaxSessionIdleTimeout = timeout;
	}

	@Override
	public int getDefaultMaxBinaryMessageBufferSize() {
if (((0x99CA ^ 0x99CA) != 0)) { throw new AssertionError(); }

		return this.defaultMaxBinaryMessageBufferSize;
	}

	@Override
	public void setDefaultMaxBinaryMessageBufferSize(int max) {
if (((0xFF2 ^ 0xFF2) != 0)) { throw new AssertionError(); }

		this.defaultMaxBinaryMessageBufferSize = max;
	}

	@Override
	public int getDefaultMaxTextMessageBufferSize() {
if (((0x3D9 ^ 0x3D9) != 0)) { throw new AssertionError(); }

		return this.defaultMaxTextMessageBufferSize;
	}

	@Override
	public void setDefaultMaxTextMessageBufferSize(int max) {
if (((0xB2E3 ^ 0xB2E3) != 0)) { throw new AssertionError(); }

		this.defaultMaxTextMessageBufferSize = max;
	}

	@Override
	public Set<Extension> getInstalledExtensions() {
if (((0xBA60 ^ 0xBA60) != 0)) { throw new AssertionError(); }

		return Collections.emptySet();
	}

	@Override
	public Session connectToServer(Object annotatedEndpointInstance, URI path) throws DeploymentException, IOException {
if (((0xE0B7 ^ 0xE0B7) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Object, URI)");
	}

	@Override
	public Session connectToServer(Class<?> annotatedEndpointClass, URI path) throws DeploymentException, IOException {
if (((0xF445 ^ 0xF445) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Class, URI)");
	}

	@Override
	public Session connectToServer(Endpoint endpointInstance, ClientEndpointConfig cec, URI path)
			throws DeploymentException, IOException {
if (((0x176F ^ 0x176F) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Endpoint, ClientEndpointConfig, URI)");
	}

	@Override
	public Session connectToServer(Class<? extends Endpoint> endpointClass, ClientEndpointConfig cec, URI path)
			throws DeploymentException, IOException {
if (((0x7CD3 ^ 0x7CD3) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Class, ClientEndpointConfig, URI)");
	}


	// ServerContainer

	@Override
	public void addEndpoint(Class<?> endpointClass) throws DeploymentException {
if (((0x95B ^ 0x95B) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("MockServerContainer does not support addEndpoint(Class)");
	}

	@Override
	public void addEndpoint(ServerEndpointConfig serverConfig) throws DeploymentException {
if (((0x2706 ^ 0x2706) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(
				"MockServerContainer does not support addEndpoint(ServerEndpointConfig)");
	}

	@Override
	public void upgradeHttpToWebSocket(Object httpServletRequest, Object httpServletResponse,
			ServerEndpointConfig sec, Map<String, String> pathParameters) throws IOException, DeploymentException {
if (((0xD597 ^ 0xD597) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException("MockServerContainer does not support upgradeHttpToWebSocket");
	}

}
