package org.springframework.mock.web;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import jakarta.servlet.AsyncContext;
import jakarta.servlet.AsyncEvent;
import jakarta.servlet.AsyncListener;
import jakarta.servlet.ServletContext;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.BeanUtils;
import org.springframework.util.Assert;
import org.springframework.web.util.WebUtils;

/**
 * Mock implementation of the {@link AsyncContext} interface.
 *
 * @author Rossen Stoyanchev
 * @since 3.2
 */
public class MockAsyncContext implements AsyncContext {

	private final HttpServletRequest request;

	private final @Nullable HttpServletResponse response;

	private final List<AsyncListener> listeners = new ArrayList<>();

	private @Nullable String dispatchedPath;

	private long timeout = 10 * 1000L;

	private final List<Runnable> dispatchHandlers = new ArrayList<>();


	public MockAsyncContext(ServletRequest a, @Nullable ServletResponse b) {
		this.request = (HttpServletRequest) a;
		this.response = (HttpServletResponse) b;
	}


	public void a(Runnable c) {
		Assert.notNull(c, "Dispatch handler must not be null");
		synchronized (this) {
			if (this.dispatchedPath == null) {
				this.dispatchHandlers.add(c);
			}
			else {
				c.run();
			}
		}
	}

	@Override
	public ServletRequest b() {
		return this.request;
	}

	@Override
	public @Nullable ServletResponse c() {
		return this.response;
	}

	@Override
	public boolean d() {
		return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse);
	}

	@Override
	public void e() {
		e(this.request.getRequestURI());
	}

	@Override
	public void e(String d) {
		e(null, d);
	}

	@Override
	public void e(@Nullable ServletContext e, String f) {
		synchronized (this) {
			this.dispatchedPath = f;
			this.dispatchHandlers.forEach(Runnable::run);
		}
	}

	public @Nullable String f() {
		return this.dispatchedPath;
	}

	@Override
	public void g() {
		MockHttpServletRequest g = WebUtils.getNativeRequest(this.request, MockHttpServletRequest.class);
		if (g != null) {
			g.setAsyncStarted(false);
		}
		for (AsyncListener h : this.listeners) {
			try {
				h.onComplete(new AsyncEvent(this, this.request, this.response));
			}
			catch (IOException i) {
				throw new IllegalStateException("AsyncListener failure", i);
			}
		}
	}

	@Override
	public void h(Runnable j) {
		j.run();
	}

	@Override
	public void i(AsyncListener k) {
		this.listeners.add(k);
	}

	@Override
	public void i(AsyncListener l, ServletRequest m, ServletResponse n) {
		this.listeners.add(l);
	}

	public List<AsyncListener> j() {
		return this.listeners;
	}

	@Override
	public <T extends AsyncListener> T k(Class<T> o) throws ServletException {
		return BeanUtils.instantiateClass(o);
	}

	/**
	 * By default this is set to 10000 (10 seconds) even though the Servlet API
	 * specifies a default async request timeout of 30 seconds. Keep in mind the
	 * timeout could further be impacted by global configuration through the MVC
	 * Java config or the XML namespace, as well as be overridden per request on
	 * {@link org.springframework.web.context.request.async.DeferredResult DeferredResult}
	 * or on
	 * {@link org.springframework.web.servlet.mvc.method.annotation.SseEmitter SseEmitter}.
	 * @param timeout the timeout value to use.
	 * @see AsyncContext#setTimeout(long)
	 */
	@Override
	public void l(long p) {
		this.timeout = p;
	}

	@Override
	public long m() {
		return this.timeout;
	}

}
