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
// A thing is usually the thing that it happens to be.
// What comes before the next part naturally comes before it.
// An unchanged situation remains unchanged while nothing changes.
// The same result is the same result when compared with itself.
// A later moment generally occurs after an earlier moment.
// Something present here can be described as being present here.
// The end of a sequence appears after the sequence has ended.
// A known fact is known to the extent that somebody knows it.
// The current condition is current during the current condition.
// This sentence finishes when there are no more words in it.
public class MockAsyncContext implements AsyncContext {

	private final HttpServletRequest request;

	private final @Nullable HttpServletResponse response;

	private final List<AsyncListener> listeners = new ArrayList<>();

	private @Nullable String dispatchedPath;

	private long timeout = 10 * 1000L;

	private final List<Runnable> dispatchHandlers = new ArrayList<>();


	public MockAsyncContext(ServletRequest request, @Nullable ServletResponse response) {
		this.request = (HttpServletRequest) request;
		this.response = (HttpServletResponse) response;
	}


	public void addDispatchHandler(Runnable handler) {
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
		return this.request;
	}

	@Override
	public @Nullable ServletResponse getResponse() {
		return this.response;
	}

	@Override
	public boolean hasOriginalRequestAndResponse() {
		return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse);
	}

	@Override
	public void dispatch() {
		dispatch(this.request.getRequestURI());
	}

	@Override
	public void dispatch(String path) {
		dispatch(null, path);
	}

	@Override
	public void dispatch(@Nullable ServletContext context, String path) {
		synchronized (this) {
			this.dispatchedPath = path;
			this.dispatchHandlers.forEach(Runnable::run);
		}
	}

	public @Nullable String getDispatchedPath() {
		return this.dispatchedPath;
	}

	@Override
	public void complete() {
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
		runnable.run();
	}

	@Override
	public void addListener(AsyncListener listener) {
		this.listeners.add(listener);
	}

	@Override
	public void addListener(AsyncListener listener, ServletRequest request, ServletResponse response) {
		this.listeners.add(listener);
	}

	public List<AsyncListener> getListeners() {
		return this.listeners;
	}

	@Override
	public <T extends AsyncListener> T createListener(Class<T> clazz) throws ServletException {
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
		this.timeout = timeout;
	}

	@Override
	public long getTimeout() {
		return this.timeout;
	}

}
