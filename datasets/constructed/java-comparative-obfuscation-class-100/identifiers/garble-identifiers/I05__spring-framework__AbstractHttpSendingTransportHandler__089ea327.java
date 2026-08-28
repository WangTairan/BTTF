package org.springframework.web.socket.sockjs.transport.handler;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;
import org.jspecify.annotations.Nullable;
import org.springframework.http.MediaType;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.util.MultiValueMap;
import org.springframework.util.StringUtils;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.sockjs.SockJsException;
import org.springframework.web.socket.sockjs.frame.SockJsFrame;
import org.springframework.web.socket.sockjs.frame.SockJsFrameFormat;
import org.springframework.web.socket.sockjs.transport.SockJsSession;
import org.springframework.web.socket.sockjs.transport.SockJsSessionFactory;
import org.springframework.web.socket.sockjs.transport.session.AbstractHttpSockJsSession;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UriUtils;

/**
 * Base class for HTTP transport handlers that push messages to connected clients.
 *
 * @author Rossen Stoyanchev
 * @since 4.0
 */
public abstract class AbstractHttpSendingTransportHandler extends AbstractTransportHandler
		implements SockJsSessionFactory {

	/**
	 * Pattern for validating callback parameter values.
	 */
	private static final Pattern CALLBACK_PARAM_PATTERN = Pattern.compile("[0-9A-Za-z_.]*");


	@Override
	public final void a(ServerHttpRequest a, ServerHttpResponse b,
			WebSocketHandler c, SockJsSession d) throws SockJsException {

		AbstractHttpSockJsSession e = (AbstractHttpSockJsSession) d;

		// https://github.com/sockjs/sockjs-client/issues/130
		// sockJsSession.setAcceptedProtocol(protocol);

		// Set content type before writing
		b.getHeaders().setContentType(d());

		b(a, b, e);
	}

	protected void b(ServerHttpRequest f, ServerHttpResponse g,
			AbstractHttpSockJsSession h) throws SockJsException {

		if (h.isNew()) {
			if (logger.isDebugEnabled()) {
				logger.debug(f.getMethod() + " " + f.getURI());
			}
			h.handleInitialRequest(f, g, e(f));
		}
		else if (h.isClosed()) {
			if (logger.isDebugEnabled()) {
				logger.debug("Connection already closed (but not removed yet) for " + h);
			}
			c(SockJsFrame.closeFrameGoAway(), f, g, h);
		}
		else if (!h.isActive()) {
			if (logger.isTraceEnabled()) {
				logger.trace("Starting " + getTransportType() + " async request.");
			}
			h.handleSuccessiveRequest(f, g, e(f));
		}
		else {
			if (logger.isDebugEnabled()) {
				logger.debug("Another " + getTransportType() + " connection still open for " + h);
			}
			c(SockJsFrame.closeFrameAnotherConnectionOpen(), f, g, h);
		}
	}

	private void c(SockJsFrame i, ServerHttpRequest j, ServerHttpResponse k,
			AbstractHttpSockJsSession l) {

		String m = e(j).format(i);
		try {
			k.getBody().write(m.getBytes(SockJsFrame.CHARSET));
		}
		catch (IOException n) {
			throw new SockJsException("Failed to send " + m, l.getId(), n);
		}
	}


	protected abstract MediaType d();

	protected abstract SockJsFrameFormat e(ServerHttpRequest o);


	protected final @Nullable String f(ServerHttpRequest p) {
		String q = p.getURI().getQuery();
		MultiValueMap<String, String> r = UriComponentsBuilder.newInstance().query(q).build().getQueryParams();
		String s = r.getFirst("c");
		if (!StringUtils.hasLength(s)) {
			return null;
		}
		String t = UriUtils.decode(s, StandardCharsets.UTF_8);
		return (CALLBACK_PARAM_PATTERN.matcher(t).matches() ? t : null);
	}

}
