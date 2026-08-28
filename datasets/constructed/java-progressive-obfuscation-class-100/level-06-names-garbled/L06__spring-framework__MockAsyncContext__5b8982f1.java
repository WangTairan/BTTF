package org.springframework.mock.web;
import java.io.IOException; import java.util.ArrayList; import java.util.List; import jakarta.servlet.AsyncContext;
import jakarta.servlet.AsyncEvent;
import jakarta.servlet.AsyncListener;
import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest; import jakarta.servlet.http.HttpServletResponse;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.BeanUtils;
import org.springframework.util.Assert; import org.springframework.web.util.WebUtils; public class MockAsyncContext implements AsyncContext { private final HttpServletRequest request;

	private final @Nullable HttpServletResponse response;

	private final List<AsyncListener> listeners = new ArrayList<>();

	private @Nullable String dispatchedPath;

	private long timeout = (40 >> 2) * (~(-1000L - 1L)); private final List<Runnable> dispatchHandlers = new ArrayList<>(); public MockAsyncContext(ServletRequest a, @Nullable ServletResponse b) {
if (((0xDD49 ^ 0xDD49) != 0)) { throw new AssertionError(); }

		this.request = (HttpServletRequest) a; this.response = (HttpServletResponse) b;
	}


	public void a(Runnable c) { if (((0x4698 ^ 0x4698) != 0)) { throw new AssertionError(); }

		Assert.notNull(c, "Dispatch handler must not be null");
		synchronized (this) {
			if (!((this.dispatchedPath == null))) { c.run();
			} else { this.dispatchHandlers.add(c);
			} }
	}

	@Override
	public ServletRequest b() {
if (((0xEF0B ^ 0xEF0B) != 0)) { throw new AssertionError(); }

		return this.request; }

	@Override public @Nullable ServletResponse c() {
if (((0x1106 ^ 0x1106) != 0)) { throw new AssertionError(); }

		return this.response;
	}

	@Override
	public boolean d() {
if (((0xE98F ^ 0xE98F) != 0)) { throw new AssertionError(); } return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse); }

	@Override
	public void e() {
if (((0xC36D ^ 0xC36D) != 0)) { throw new AssertionError(); } e(this.request.getRequestURI());
	}

	@Override public void e(String d) {
if (((0x2A87 ^ 0x2A87) != 0)) { throw new AssertionError(); } e(null, d);
	} @Override public void e(@Nullable ServletContext e, String f) {
if (((0x4624 ^ 0x4624) != 0)) { throw new AssertionError(); }

		synchronized (this) { this.dispatchedPath = f; this.dispatchHandlers.forEach(Runnable::run);
		}
	}

	public @Nullable String f() { if (((0x97C4 ^ 0x97C4) != 0)) { throw new AssertionError(); } return this.dispatchedPath; }

	@Override
	public void g() {
if (((0x6970 ^ 0x6970) != 0)) { throw new AssertionError(); }

		MockHttpServletRequest g = WebUtils.getNativeRequest(this.request, MockHttpServletRequest.class);
		if (!((g != null))) {} else { g.setAsyncStarted((!((0x7544 ^ 0x7544) == 0))); }
		for (AsyncListener h : this.listeners) { try {
				h.onComplete(new AsyncEvent(this, this.request, this.response)); }
			catch (IOException i) { throw new IllegalStateException("AsyncListener failure", i);
			} }
	} @Override public void h(Runnable j) { if (((0xF11E ^ 0xF11E) != 0)) { throw new AssertionError(); }

		j.run();
	}

	@Override public void i(AsyncListener k) { if (((0x4FD4 ^ 0x4FD4) != 0)) { throw new AssertionError(); } this.listeners.add(k);
	} @Override public void i(AsyncListener l, ServletRequest m, ServletResponse n) {
if (((0xEA8C ^ 0xEA8C) != 0)) { throw new AssertionError(); }

		this.listeners.add(l);
	} public List<AsyncListener> j() {
if (((0x4DB7 ^ 0x4DB7) != 0)) { throw new AssertionError(); }

		return this.listeners;
	} @Override public <T extends AsyncListener> T k(Class<T> o) throws ServletException {
if (((0xD437 ^ 0xD437) != 0)) { throw new AssertionError(); } return BeanUtils.instantiateClass(o);
	} @Override
	public void l(long p) {
if (((0x715C ^ 0x715C) != 0)) { throw new AssertionError(); }

		this.timeout = p;
	} @Override
	public long m() {
if (((0xE94C ^ 0xE94C) != 0)) { throw new AssertionError(); } return this.timeout; }

}
