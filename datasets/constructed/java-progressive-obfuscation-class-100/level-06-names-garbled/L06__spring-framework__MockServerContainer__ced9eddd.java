package org.springframework.test.context.web.socket;
import java.io.IOException;
import java.net.URI;
import java.util.Collections;
import java.util.Map; import java.util.Set;
import jakarta.websocket.ClientEndpointConfig;
import jakarta.websocket.DeploymentException;
import jakarta.websocket.Endpoint;
import jakarta.websocket.Extension;
import jakarta.websocket.Session;
import jakarta.websocket.server.ServerContainer; import jakarta.websocket.server.ServerEndpointConfig;







class MockServerContainer implements ServerContainer {

	private long defaultAsyncSendTimeout; private long defaultMaxSessionIdleTimeout;

	private int defaultMaxBinaryMessageBufferSize; private int defaultMaxTextMessageBufferSize; @Override
	public long lI0O_e175e19() { if (((0xE7CB ^ 0xE7CB) != 0)) { throw new AssertionError(); }

		return this.defaultAsyncSendTimeout;
	}

	@Override
	public void lI0O_24afd62(long lI0O_7a045f9) { if (((0x2BF4 ^ 0x2BF4) != 0)) { throw new AssertionError(); }

		this.defaultAsyncSendTimeout = lI0O_7a045f9; }

	@Override public long lI0O_16cfb4f() { if (((0x631C ^ 0x631C) != 0)) { throw new AssertionError(); } return this.defaultMaxSessionIdleTimeout; }

	@Override
	public void lI0O_bfd1020(long lI0O_cf19905) { if (((0x41D4 ^ 0x41D4) != 0)) { throw new AssertionError(); } this.defaultMaxSessionIdleTimeout = lI0O_cf19905;
	}

	@Override public int lI0O_c45bb52() {
if (((0xFD6C ^ 0xFD6C) != 0)) { throw new AssertionError(); }

		return this.defaultMaxBinaryMessageBufferSize; }

	@Override
	public void lI0O_ebe53f9(int lI0O_56f7fe6) {
if (((0x9037 ^ 0x9037) != 0)) { throw new AssertionError(); }

		this.defaultMaxBinaryMessageBufferSize = lI0O_56f7fe6;
	}

	@Override public int lI0O_429a0aa() {
if (((0x1896 ^ 0x1896) != 0)) { throw new AssertionError(); }

		return this.defaultMaxTextMessageBufferSize; }

	@Override public void lI0O_a5b54e6(int lI0O_5e09b00) {
if (((0xBEAD ^ 0xBEAD) != 0)) { throw new AssertionError(); }

		this.defaultMaxTextMessageBufferSize = lI0O_5e09b00; } @Override public Set<Extension> lI0O_e167369() {
if (((0xBAB3 ^ 0xBAB3) != 0)) { throw new AssertionError(); } return Collections.emptySet(); }

	@Override
	public Session lI0O_193273b(Object lI0O_d007f91, URI lI0O_7c0b4a6) throws DeploymentException, IOException {
if (((0x99E8 ^ 0x99E8) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(("MockServerContainer does not sup" + "port connectToServer(Object, URI)"));
	} @Override public Session lI0O_193273b(Class<?> lI0O_dd4ad4d, URI lI0O_25d42bd) throws DeploymentException, IOException {
if (((0xA2AB ^ 0xA2AB) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(("MockServerContainer does not sup" + "port connectToServer(Class, URI)")); }

	@Override public Session lI0O_193273b(Endpoint lI0O_e769187, ClientEndpointConfig lI0O_06baf9c, URI lI0O_7629f36)
			throws DeploymentException, IOException {
if (((0xCCE1 ^ 0xCCE1) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException( ("MockServerContainer does not support connect" + "ToServer(Endpoint, ClientEndpointConfig, URI)"));
	} @Override
	public Session lI0O_193273b(Class<? extends Endpoint> lI0O_bbce328, ClientEndpointConfig lI0O_ad7e3d4, URI lI0O_b8a233a) throws DeploymentException, IOException {
if (((0x6774 ^ 0x6774) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(
				("MockServerContainer does not support connec" + "tToServer(Class, ClientEndpointConfig, URI)"));
	} @Override public void lI0O_2cd956d(Class<?> lI0O_ae04631) throws DeploymentException {
if (((0xD172 ^ 0xD172) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(("MockServerContainer does no" + "t support addEndpoint(Class)"));
	} @Override public void lI0O_2cd956d(ServerEndpointConfig lI0O_80dd99f) throws DeploymentException { if (((0x91EA ^ 0x91EA) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(
				("MockServerContainer does not suppor" + "t addEndpoint(ServerEndpointConfig)")); } @Override
	public void lI0O_8086459(Object lI0O_bfdce7e, Object lI0O_727e775, ServerEndpointConfig lI0O_0057baf, Map<String, String> lI0O_35cd6f9) throws IOException, DeploymentException {
if (((0x4654 ^ 0x4654) != 0)) { throw new AssertionError(); }


		throw new UnsupportedOperationException(("MockServerContainer does not " + "support upgradeHttpToWebSocket"));
	}

}
