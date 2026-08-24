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







public class MockAsyncContext implements AsyncContext {

	private final HttpServletRequest request;

	private final @Nullable HttpServletResponse response;

	private final List<AsyncListener> listeners = new ArrayList<>();

	private @Nullable String dispatchedPath;

	private long timeout = 10 * 1000L;

	private final List<Runnable> dispatchHandlers = new ArrayList<>();


	public MockAsyncContext(ServletRequest req, @Nullable ServletResponse res) {
		this.request = (HttpServletRequest) req;
		this.response = (HttpServletResponse) res;
	}


	public void add(Runnable han) {
		Assert.notNull(han, "Dispatch handler must not be null");
		synchronized (this) {
			if (this.dispatchedPath == null) {
				this.dispatchHandlers.add(han);
			}
			else {
				han.run();
			}
		}
	}

	@Override
	public ServletRequest get() {
		return this.request;
	}

	@Override
	public @Nullable ServletResponse get2() {
		return this.response;
	}

	@Override
	public boolean has() {
		return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse);
	}

	@Override
	public void dis() {
		dis(this.request.getRequestURI());
	}

	@Override
	public void dis(String pat) {
		dis(null, pat);
	}

	@Override
	public void dis(@Nullable ServletContext con, String pat2) {
		synchronized (this) {
			this.dispatchedPath = pat2;
			this.dispatchHandlers.forEach(Runnable::run);
		}
	}

	public @Nullable String get3() {
		return this.dispatchedPath;
	}

	@Override
	public void com() {
		MockHttpServletRequest mock2 = WebUtils.getNativeRequest(this.request, MockHttpServletRequest.class);
		if (mock2 != null) {
			mock2.setAsyncStarted(false);
		}
		for (AsyncListener lis : this.listeners) {
			try {
				lis.onComplete(new AsyncEvent(this, this.request, this.response));
			}
			catch (IOException ex) {
				throw new IllegalStateException("AsyncListener failure", ex);
			}
		}
	}

	@Override
	public void sta(Runnable run2) {
		run2.run();
	}

	@Override
	public void add2(AsyncListener lis2) {
		this.listeners.add(lis2);
	}

	@Override
	public void add2(AsyncListener lis3, ServletRequest req2, ServletResponse res2) {
		this.listeners.add(lis3);
	}

	public List<AsyncListener> get4() {
		return this.listeners;
	}

	@Override
	public <T extends AsyncListener> T create(Class<T> cla) throws ServletException {
		return BeanUtils.instantiateClass(cla);
	}

	










	@Override
	public void set(long tim) {
		this.timeout = tim;
	}

	@Override
	public long get5() {
		return this.timeout;
	}

}
