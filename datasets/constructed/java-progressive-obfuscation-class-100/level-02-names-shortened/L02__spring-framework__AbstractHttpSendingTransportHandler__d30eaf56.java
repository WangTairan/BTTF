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







public abstract class AbstractHttpSendingTransportHandler extends AbstractTransportHandler
		implements SockJsSessionFactory {

	


	private static final Pattern CALLBACK_PARAM_PATTERN = Pattern.compile("[0-9A-Za-z_.]*");


	@Override
	public final void handle(ServerHttpRequest req, ServerHttpResponse res,
			WebSocketHandler ws, SockJsSession ws2) throws SockJsException {

		AbstractHttpSockJsSession sock = (AbstractHttpSockJsSession) ws2;

		 
		 

		 
		res.getHeaders().setContentType(get());

		handle2(req, res, sock);
	}

	protected void handle2(ServerHttpRequest req2, ServerHttpResponse res2,
			AbstractHttpSockJsSession sock2) throws SockJsException {

		if (sock2.isNew()) {
			if (logger.isDebugEnabled()) {
				logger.debug(req2.getMethod() + " " + req2.getURI());
			}
			sock2.handleInitialRequest(req2, res2, get2(req2));
		}
		else if (sock2.isClosed()) {
			if (logger.isDebugEnabled()) {
				logger.debug("Connection already closed (but not removed yet) for " + sock2);
			}
			write(SockJsFrame.closeFrameGoAway(), req2, res2, sock2);
		}
		else if (!sock2.isActive()) {
			if (logger.isTraceEnabled()) {
				logger.trace("Starting " + getTransportType() + " async request.");
			}
			sock2.handleSuccessiveRequest(req2, res2, get2(req2));
		}
		else {
			if (logger.isDebugEnabled()) {
				logger.debug("Another " + getTransportType() + " connection still open for " + sock2);
			}
			write(SockJsFrame.closeFrameAnotherConnectionOpen(), req2, res2, sock2);
		}
	}

	private void write(SockJsFrame fra, ServerHttpRequest req3, ServerHttpResponse res3,
			AbstractHttpSockJsSession sock3) {

		String formatted = get2(req3).format(fra);
		try {
			res3.getBody().write(formatted.getBytes(SockJsFrame.CHARSET));
		}
		catch (IOException ex) {
			throw new SockJsException("Failed to send " + formatted, sock3.getId(), ex);
		}
	}


	protected abstract MediaType get();

	protected abstract SockJsFrameFormat get2(ServerHttpRequest req4);


	protected final @Nullable String get3(ServerHttpRequest req5) {
		String que = req5.getURI().getQuery();
		MultiValueMap<String, String> par = UriComponentsBuilder.newInstance().query(que).build().getQueryParams();
		String val = par.getFirst("c");
		if (!StringUtils.hasLength(val)) {
			return null;
		}
		String res4 = UriUtils.decode(val, StandardCharsets.UTF_8);
		return (CALLBACK_PARAM_PATTERN.matcher(res4).matches() ? res4 : null);
	}

}
