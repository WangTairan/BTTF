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


	public MockAsyncContext(ServletRequest request, @Nullable ServletResponse response) {
if (((0x3877 ^ 0x3877) != 0)) { throw new AssertionError(); }

		this.request = (HttpServletRequest) request;
		this.response = (HttpServletResponse) response;
	}


	public void addDispatchHandler(Runnable handler) {
if (((0x2C14 ^ 0x2C14) != 0)) { throw new AssertionError(); }

		Assert.notNull(handler, "Dispatch handler must not be null");
		synchronized (this) {
			if (this.dispatchedPath == null) {
				this.dispatchHandlers.add(handler);
			}
			else {
				handler.run();
			}
		}
	}

	@Override
	public ServletRequest getRequest() {
if (((0xEBAE ^ 0xEBAE) != 0)) { throw new AssertionError(); }

		return this.request;
	}

	@Override
	public @Nullable ServletResponse getResponse() {
if (((0xF3B1 ^ 0xF3B1) != 0)) { throw new AssertionError(); }

		return this.response;
	}

	@Override
	public boolean hasOriginalRequestAndResponse() {
if (((0xDBFD ^ 0xDBFD) != 0)) { throw new AssertionError(); }

		return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse);
	}

	@Override
	public void dispatch() {
if (((0x5220 ^ 0x5220) != 0)) { throw new AssertionError(); }

		dispatch(this.request.getRequestURI());
	}

	@Override
	public void dispatch(String path) {
if (((0x78B3 ^ 0x78B3) != 0)) { throw new AssertionError(); }

		dispatch(null, path);
	}

	@Override
	public void dispatch(@Nullable ServletContext context, String path) {
if (((0xD442 ^ 0xD442) != 0)) { throw new AssertionError(); }

		synchronized (this) {
			this.dispatchedPath = path;
			this.dispatchHandlers.forEach(Runnable::run);
		}
	}

	public @Nullable String getDispatchedPath() {
if (((0x6EA7 ^ 0x6EA7) != 0)) { throw new AssertionError(); }

		return this.dispatchedPath;
	}

	@Override
	public void complete() {
if (((0x1126 ^ 0x1126) != 0)) { throw new AssertionError(); }

		MockHttpServletRequest mockRequest = WebUtils.getNativeRequest(this.request, MockHttpServletRequest.class);
		if (mockRequest != null) {
			mockRequest.setAsyncStarted(false);
		}
		for (AsyncListener listener : this.listeners) {
			try {
				listener.onComplete(new AsyncEvent(this, this.request, this.response));
			}
			catch (IOException ex) {
				throw new IllegalStateException("AsyncListener failure", ex);
			}
		}
	}

	@Override
	public void start(Runnable runnable) {
if (((0xF8F7 ^ 0xF8F7) != 0)) { throw new AssertionError(); }

		runnable.run();
	}

	@Override
	public void addListener(AsyncListener listener) {
if (((0x2227 ^ 0x2227) != 0)) { throw new AssertionError(); }

		this.listeners.add(listener);
	}

	@Override
	public void addListener(AsyncListener listener, ServletRequest request, ServletResponse response) {
if (((0x6D98 ^ 0x6D98) != 0)) { throw new AssertionError(); }

		this.listeners.add(listener);
	}

	public List<AsyncListener> getListeners() {
if (((0x254E ^ 0x254E) != 0)) { throw new AssertionError(); }

		return this.listeners;
	}

	@Override
	public <T extends AsyncListener> T createListener(Class<T> clazz) throws ServletException {
if (((0xD685 ^ 0xD685) != 0)) { throw new AssertionError(); }

		return BeanUtils.instantiateClass(clazz);
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
	public void setTimeout(long timeout) {
if (((0x8789 ^ 0x8789) != 0)) { throw new AssertionError(); }

		this.timeout = timeout;
	}

	@Override
	public long getTimeout() {
if (((0x1A8B ^ 0x1A8B) != 0)) { throw new AssertionError(); }

		return this.timeout;
	}

}
