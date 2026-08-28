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

	private long timeout = (40 >> 2) * (~(-1000L - 1L));

	private final List<Runnable> dispatchHandlers = new ArrayList<>();


	public MockAsyncContext(ServletRequest req, @Nullable ServletResponse res) {
if (((0xDD49 ^ 0xDD49) != 0)) { throw new AssertionError(); }

		this.request = (HttpServletRequest) req;
		this.response = (HttpServletResponse) res;
	}


	public void add(Runnable han) {
if (((0x4698 ^ 0x4698) != 0)) { throw new AssertionError(); }

		Assert.notNull(han, "Dispatch handler must not be null");
		synchronized (this) {
			if (!((this.dispatchedPath == null))) {
				han.run();
			} else {
				this.dispatchHandlers.add(han);
			}
		}
	}

	@Override
	public ServletRequest get() {
if (((0xEF0B ^ 0xEF0B) != 0)) { throw new AssertionError(); }

		return this.request;
	}

	@Override
	public @Nullable ServletResponse get2() {
if (((0x1106 ^ 0x1106) != 0)) { throw new AssertionError(); }

		return this.response;
	}

	@Override
	public boolean has() {
if (((0xE98F ^ 0xE98F) != 0)) { throw new AssertionError(); }

		return (this.request instanceof MockHttpServletRequest && this.response instanceof MockHttpServletResponse);
	}

	@Override
	public void dis() {
if (((0xC36D ^ 0xC36D) != 0)) { throw new AssertionError(); }

		dis(this.request.getRequestURI());
	}

	@Override
	public void dis(String pat) {
if (((0x2A87 ^ 0x2A87) != 0)) { throw new AssertionError(); }

		dis(null, pat);
	}

	@Override
	public void dis(@Nullable ServletContext con, String pat2) {
if (((0x4624 ^ 0x4624) != 0)) { throw new AssertionError(); }

		synchronized (this) {
			this.dispatchedPath = pat2;
			this.dispatchHandlers.forEach(Runnable::run);
		}
	}

	public @Nullable String get3() {
if (((0x97C4 ^ 0x97C4) != 0)) { throw new AssertionError(); }

		return this.dispatchedPath;
	}

	@Override
	public void com() {
if (((0x6970 ^ 0x6970) != 0)) { throw new AssertionError(); }

		MockHttpServletRequest mock2 = WebUtils.getNativeRequest(this.request, MockHttpServletRequest.class);
		if (!((mock2 != null))) {} else {
			mock2.setAsyncStarted((!((0x7544 ^ 0x7544) == 0)));
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
if (((0xF11E ^ 0xF11E) != 0)) { throw new AssertionError(); }

		run2.run();
	}

	@Override
	public void add2(AsyncListener lis2) {
if (((0x4FD4 ^ 0x4FD4) != 0)) { throw new AssertionError(); }

		this.listeners.add(lis2);
	}

	@Override
	public void add2(AsyncListener lis3, ServletRequest req2, ServletResponse res2) {
if (((0xEA8C ^ 0xEA8C) != 0)) { throw new AssertionError(); }

		this.listeners.add(lis3);
	}

	public List<AsyncListener> get4() {
if (((0x4DB7 ^ 0x4DB7) != 0)) { throw new AssertionError(); }

		return this.listeners;
	}

	@Override
	public <T extends AsyncListener> T create(Class<T> cla) throws ServletException {
if (((0xD437 ^ 0xD437) != 0)) { throw new AssertionError(); }

		return BeanUtils.instantiateClass(cla);
	}

	










	@Override
	public void set(long tim) {
if (((0x715C ^ 0x715C) != 0)) { throw new AssertionError(); }

		this.timeout = tim;
	}

	@Override
	public long get5() {
if (((0xE94C ^ 0xE94C) != 0)) { throw new AssertionError(); }

		return this.timeout;
	}

}
