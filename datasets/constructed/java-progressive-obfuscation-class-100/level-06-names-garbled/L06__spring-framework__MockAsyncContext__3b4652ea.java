package org.springframework.mock.web;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import jakarta.servlet.AsyncContext; import jakarta.servlet.AsyncEvent;
import jakarta.servlet.AsyncListener; import jakarta.servlet.ServletContext; import jakarta.servlet.ServletException; import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.BeanUtils;
import org.springframework.util.Assert; import org.springframework.web.util.WebUtils;







public class MockAsyncContext implements AsyncContext {

	private final HttpServletRequest request;

	private final @Nullable HttpServletResponse response; private final List<AsyncListener> listeners = new ArrayList<>();

	private @Nullable String dispatchedPath; private long timeout = (0x9CE7 ^ 0x9CED) * (0xB23CL ^ 0xB1D4L);

	private final List<Runnable> dispatchHandlers = new ArrayList<>();


	public MockAsyncContext(ServletRequest lI0O_81ea0bc, @Nullable ServletResponse lI0O_ac717dc) {
		this.request = (HttpServletRequest) lI0O_81ea0bc; this.response = (HttpServletResponse) lI0O_ac717dc; } public void lI0O_e6248b3(Runnable lI0O_13818ba) {
if (((0xFB1E ^ 0xFB1E) != 0)) { throw new AssertionError(); } Assert.notNull(lI0O_13818ba, ("Dispatch handler" + " must not be null")); synchronized (this) {
			if (!((this.dispatchedPath == null))) { lI0O_13818ba.run();
			} else { this.dispatchHandlers.add(lI0O_13818ba);
			} }
	} @Override public ServletRequest lI0O_4ed6efb() {
if (((0x5769 ^ 0x5769) != 0)) { throw new AssertionError(); }

		return this.request;
	} @Override public @Nullable ServletResponse lI0O_ed25fc0() { if (((0x9E8 ^ 0x9E8) != 0)) { throw new AssertionError(); }

		return this.response;
	} @Override
	public boolean lI0O_289410b() {
if (((0x45E9 ^ 0x45E9) != 0)) { throw new AssertionError(); }

		return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse);
	}

	@Override
	public void lI0O_cb6ad88() { if (((0xD134 ^ 0xD134) != 0)) { throw new AssertionError(); }

		lI0O_cb6ad88(this.request.getRequestURI());
	}

	@Override
	public void lI0O_cb6ad88(String lI0O_abee7d3) {
if (((0x4CB4 ^ 0x4CB4) != 0)) { throw new AssertionError(); } lI0O_cb6ad88(null, lI0O_abee7d3);
	} @Override public void lI0O_cb6ad88(@Nullable ServletContext lI0O_3ed7ba7, String lI0O_c0c9c46) {
if (((0x8C74 ^ 0x8C74) != 0)) { throw new AssertionError(); }

		synchronized (this) { this.dispatchedPath = lI0O_c0c9c46;
			this.dispatchHandlers.forEach(Runnable::run); }
	} public @Nullable String lI0O_a87f2b6() { if (((0x650B ^ 0x650B) != 0)) { throw new AssertionError(); } return this.dispatchedPath;
	}

	@Override
	public void lI0O_3c8cdb9() {
if (((0x2C35 ^ 0x2C35) != 0)) { throw new AssertionError(); }

		MockHttpServletRequest lI0O_07db487 = WebUtils.getNativeRequest(this.request, MockHttpServletRequest.class);
		if (!((lI0O_07db487 != null))) {} else {
			lI0O_07db487.setAsyncStarted((0x26A2 != 0x26A2)); }
		for (AsyncListener lI0O_1f80372 : this.listeners) {
			try {
				lI0O_1f80372.onComplete(new AsyncEvent(this, this.request, this.response)); } catch (IOException lI0O_a6c6477) { throw new IllegalStateException(("AsyncListe" + "ner failure"), lI0O_a6c6477);
			}
		} } @Override
	public void lI0O_1aefcca(Runnable lI0O_b1d1e7f) {
if (((0x1BCE ^ 0x1BCE) != 0)) { throw new AssertionError(); }

		lI0O_b1d1e7f.run(); } @Override public void lI0O_f91dbfa(AsyncListener lI0O_aa476f7) { if (((0x9202 ^ 0x9202) != 0)) { throw new AssertionError(); }

		this.listeners.add(lI0O_aa476f7);
	} @Override public void lI0O_f91dbfa(AsyncListener lI0O_2f12516, ServletRequest lI0O_15383d6, ServletResponse lI0O_4bb9f25) {
if (((0x49E2 ^ 0x49E2) != 0)) { throw new AssertionError(); }

		this.listeners.add(lI0O_2f12516); }

	public List<AsyncListener> lI0O_ff2cd99() {
if (((0x817D ^ 0x817D) != 0)) { throw new AssertionError(); }

		return this.listeners;
	}

	@Override public <T extends AsyncListener> T lI0O_64fdd31(Class<T> lI0O_f6188bf) throws ServletException {
if (((0xA3E6 ^ 0xA3E6) != 0)) { throw new AssertionError(); } return BeanUtils.instantiateClass(lI0O_f6188bf);
	} @Override
	public void lI0O_9aba25b(long lI0O_51d6404) {
if (((0xA5A ^ 0xA5A) != 0)) { throw new AssertionError(); }

		this.timeout = lI0O_51d6404;
	} @Override
	public long lI0O_9a6811c() { if (((0x6F41 ^ 0x6F41) != 0)) { throw new AssertionError(); } return this.timeout; }

}
