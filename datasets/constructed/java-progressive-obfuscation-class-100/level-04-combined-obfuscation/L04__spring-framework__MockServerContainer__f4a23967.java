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







class MockServerContainer implements ServerContainer {

	private long defaultAsyncSendTimeout;

	private long defaultMaxSessionIdleTimeout;

	private int defaultMaxBinaryMessageBufferSize;

	private int defaultMaxTextMessageBufferSize;


	 

	@Override
	public long get() {
if (((0x33F0 ^ 0x33F0) != 0)) { throw new AssertionError(); }

		return this.defaultAsyncSendTimeout;
	}

	@Override
	public void set(long tim) {
if (((0x8B3E ^ 0x8B3E) != 0)) { throw new AssertionError(); }

		this.defaultAsyncSendTimeout = tim;
	}

	@Override
	public long get2() {
if (((0xAF83 ^ 0xAF83) != 0)) { throw new AssertionError(); }

		return this.defaultMaxSessionIdleTimeout;
	}

	@Override
	public void set2(long tim2) {
if (((0x4E1B ^ 0x4E1B) != 0)) { throw new AssertionError(); }

		this.defaultMaxSessionIdleTimeout = tim2;
	}

	@Override
	public int get3() {
if (((0xEFEB ^ 0xEFEB) != 0)) { throw new AssertionError(); }

		return this.defaultMaxBinaryMessageBufferSize;
	}

	@Override
	public void set3(int max) {
if (((0x6474 ^ 0x6474) != 0)) { throw new AssertionError(); }

		this.defaultMaxBinaryMessageBufferSize = max;
	}

	@Override
	public int get4() {
if (((0xAD68 ^ 0xAD68) != 0)) { throw new AssertionError(); }

		return this.defaultMaxTextMessageBufferSize;
	}

	@Override
	public void set4(int max) {
if (((0x4568 ^ 0x4568) != 0)) { throw new AssertionError(); }

		this.defaultMaxTextMessageBufferSize = max;
	}

	@Override
	public Set<Extension> get5() {
if (((0xE3B2 ^ 0xE3B2) != 0)) { throw new AssertionError(); }

		return Collections.emptySet();
	}

	@Override
	public Session connect(Object annotated, URI pat) throws DeploymentException, IOException {
if (((0x6DC1 ^ 0x6DC1) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Object, URI)");
	}

	@Override
	public Session connect(Class<?> annotated2, URI pat2) throws DeploymentException, IOException {
if (((0xA081 ^ 0xA081) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("MockServerContainer does not support connectToServer(Class, URI)");
	}

	@Override
	public Session connect(Endpoint endpoint, ClientEndpointConfig cec, URI pat3)
			throws DeploymentException, IOException {
if (((0x7256 ^ 0x7256) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Endpoint, ClientEndpointConfig, URI)");
	}

	@Override
	public Session connect(Class<? extends Endpoint> endpoint2, ClientEndpointConfig cec, URI pat4)
			throws DeploymentException, IOException {
if (((0x22F2 ^ 0x22F2) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				"MockServerContainer does not support connectToServer(Class, ClientEndpointConfig, URI)");
	}


	 

	@Override
	public void add(Class<?> endpoint3) throws DeploymentException {
if (((0x436 ^ 0x436) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("MockServerContainer does not support addEndpoint(Class)");
	}

	@Override
	public void add(ServerEndpointConfig server2) throws DeploymentException {
if (((0x31A9 ^ 0x31A9) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(
				"MockServerContainer does not support addEndpoint(ServerEndpointConfig)");
	}

	@Override
	public void upgrade(Object http, Object http2,
			ServerEndpointConfig sec, Map<String, String> path) throws IOException, DeploymentException {
if (((0xD5B7 ^ 0xD5B7) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException("MockServerContainer does not support upgradeHttpToWebSocket");
	}

}
