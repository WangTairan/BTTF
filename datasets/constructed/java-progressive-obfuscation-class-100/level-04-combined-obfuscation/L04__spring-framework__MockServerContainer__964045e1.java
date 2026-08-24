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
if (((0xE7CB ^ 0xE7CB) != 0)) { throw new AssertionError(); }

		return this.defaultAsyncSendTimeout;
	}

	@Override
	public void set(long tim) {
if (((0x2BF4 ^ 0x2BF4) != 0)) { throw new AssertionError(); }

		this.defaultAsyncSendTimeout = tim;
	}

	@Override
	public long get2() {
if (((0x631C ^ 0x631C) != 0)) { throw new AssertionError(); }

		return this.defaultMaxSessionIdleTimeout;
	}

	@Override
	public void set2(long tim2) {
if (((0x41D4 ^ 0x41D4) != 0)) { throw new AssertionError(); }

		this.defaultMaxSessionIdleTimeout = tim2;
	}

	@Override
	public int get3() {
if (((0xFD6C ^ 0xFD6C) != 0)) { throw new AssertionError(); }

		return this.defaultMaxBinaryMessageBufferSize;
	}

	@Override
	public void set3(int max) {
if (((0x9037 ^ 0x9037) != 0)) { throw new AssertionError(); }

		this.defaultMaxBinaryMessageBufferSize = max;
	}

	@Override
	public int get4() {
if (((0x1896 ^ 0x1896) != 0)) { throw new AssertionError(); }

		return this.defaultMaxTextMessageBufferSize;
	}

	@Override
	public void set4(int max) {
if (((0xBEAD ^ 0xBEAD) != 0)) { throw new AssertionError(); }

		this.defaultMaxTextMessageBufferSize = max;
	}

	@Override
	public Set<Extension> get5() {
if (((0xBAB3 ^ 0xBAB3) != 0)) { throw new AssertionError(); }

		return Collections.emptySet();
	}

	@Override
	public Session connect(Object annotated, URI pat) throws DeploymentException, IOException {
if (((0x99E8 ^ 0x99E8) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(("MockServerContainer does not sup" + "port connectToServer(Object, URI)"));
	}

	@Override
	public Session connect(Class<?> annotated2, URI pat2) throws DeploymentException, IOException {
if (((0xA2AB ^ 0xA2AB) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(("MockServerContainer does not sup" + "port connectToServer(Class, URI)"));
	}

	@Override
	public Session connect(Endpoint endpoint, ClientEndpointConfig cec, URI pat3)
			throws DeploymentException, IOException {
if (((0xCCE1 ^ 0xCCE1) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				("MockServerContainer does not support connect" + "ToServer(Endpoint, ClientEndpointConfig, URI)"));
	}

	@Override
	public Session connect(Class<? extends Endpoint> endpoint2, ClientEndpointConfig cec, URI pat4)
			throws DeploymentException, IOException {
if (((0x6774 ^ 0x6774) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				("MockServerContainer does not support connec" + "tToServer(Class, ClientEndpointConfig, URI)"));
	}


	 

	@Override
	public void add(Class<?> endpoint3) throws DeploymentException {
if (((0xD172 ^ 0xD172) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(("MockServerContainer does no" + "t support addEndpoint(Class)"));
	}

	@Override
	public void add(ServerEndpointConfig server2) throws DeploymentException {
if (((0x91EA ^ 0x91EA) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(
				("MockServerContainer does not suppor" + "t addEndpoint(ServerEndpointConfig)"));
	}

	@Override
	public void upgrade(Object http, Object http2,
			ServerEndpointConfig sec, Map<String, String> path) throws IOException, DeploymentException {
if (((0x4654 ^ 0x4654) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(("MockServerContainer does not " + "support upgradeHttpToWebSocket"));
	}

}
