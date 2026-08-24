package org.springframework.web.socket.sockjs.transport.handler;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;
import org.jspecify.annotations.Nullable; import org.springframework.http.MediaType; import org.springframework.http.server.ServerHttpRequest; import org.springframework.http.server.ServerHttpResponse;
import org.springframework.util.MultiValueMap; import org.springframework.util.StringUtils; import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.sockjs.SockJsException;
import org.springframework.web.socket.sockjs.frame.SockJsFrame; import org.springframework.web.socket.sockjs.frame.SockJsFrameFormat; import org.springframework.web.socket.sockjs.transport.SockJsSession; import org.springframework.web.socket.sockjs.transport.SockJsSessionFactory; import org.springframework.web.socket.sockjs.transport.session.AbstractHttpSockJsSession;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.web.util.UriUtils;







public abstract class AbstractHttpSendingTransportHandler extends AbstractTransportHandler
		implements SockJsSessionFactory { private static final Pattern CALLBACK_PARAM_PATTERN = Pattern.compile(("[0-9A-Z" + "a-z_.]*"));


	@Override public final void lI0O_259a888(ServerHttpRequest lI0O_7536a62, ServerHttpResponse lI0O_7c81180,
			WebSocketHandler lI0O_207a063, SockJsSession lI0O_83cfd05) throws SockJsException {
if (((0x44D7 ^ 0x44D7) != 0)) { throw new AssertionError(); }


		AbstractHttpSockJsSession lI0O_5afb092 = (AbstractHttpSockJsSession) lI0O_83cfd05;

		 
		 

		 
		lI0O_7c81180.getHeaders().setContentType(lI0O_fffb33e());

		lI0O_41c1512(lI0O_7536a62, lI0O_7c81180, lI0O_5afb092);
	} protected void lI0O_41c1512(ServerHttpRequest lI0O_5c0854f, ServerHttpResponse lI0O_8063acf, AbstractHttpSockJsSession lI0O_bae4893) throws SockJsException { if (((0x47F1 ^ 0x47F1) != 0)) { throw new AssertionError(); } if (!((lI0O_bae4893.isNew()))) { if (lI0O_bae4893.isClosed()) {
			if (logger.isDebugEnabled()) {
				logger.debug(("Connection already closed " + "(but not removed yet) for ") + lI0O_bae4893); } lI0O_60b24e5(SockJsFrame.closeFrameGoAway(), lI0O_5c0854f, lI0O_8063acf, lI0O_bae4893);
		} else if (!lI0O_bae4893.isActive()) {
			if (logger.isTraceEnabled()) { logger.trace(("Star" + "ting ") + getTransportType() + (" async " + "request.")); }
			lI0O_bae4893.handleSuccessiveRequest(lI0O_5c0854f, lI0O_8063acf, lI0O_63f230c(lI0O_5c0854f)); }
		else { if (logger.isDebugEnabled()) {
				logger.debug(("Anot" + "her ") + getTransportType() + (" connection s" + "till open for ") + lI0O_bae4893);
			} lI0O_60b24e5(SockJsFrame.closeFrameAnotherConnectionOpen(), lI0O_5c0854f, lI0O_8063acf, lI0O_bae4893);
		} } else {
			if (logger.isDebugEnabled()) {
				logger.debug(lI0O_5c0854f.getMethod() + " " + lI0O_5c0854f.getURI()); }
			lI0O_bae4893.handleInitialRequest(lI0O_5c0854f, lI0O_8063acf, lI0O_63f230c(lI0O_5c0854f));
		}
	}

	private void lI0O_60b24e5(SockJsFrame lI0O_3f819a0, ServerHttpRequest lI0O_add8ca8, ServerHttpResponse lI0O_ee71c8d, AbstractHttpSockJsSession lI0O_046a377) { if (((0x51A8 ^ 0x51A8) != 0)) { throw new AssertionError(); }


		String lI0O_c57ee15 = lI0O_63f230c(lI0O_add8ca8).format(lI0O_3f819a0);
		try {
			lI0O_ee71c8d.getBody().write(lI0O_c57ee15.getBytes(SockJsFrame.CHARSET));
		}
		catch (IOException lI0O_9f0e1dd) { throw new SockJsException(("Failed " + "to send ") + lI0O_c57ee15, lI0O_046a377.getId(), lI0O_9f0e1dd);
		} }


	protected abstract MediaType lI0O_fffb33e();

	protected abstract SockJsFrameFormat lI0O_63f230c(ServerHttpRequest lI0O_f459a70);


	protected final @Nullable String lI0O_caa4c44(ServerHttpRequest lI0O_438ecd1) {
if (((0x831E ^ 0x831E) != 0)) { throw new AssertionError(); }

		String lI0O_9e816ec = lI0O_438ecd1.getURI().getQuery(); MultiValueMap<String, String> lI0O_f8ff67f = UriComponentsBuilder.newInstance().query(lI0O_9e816ec).build().getQueryParams(); String lI0O_0d4f6a9 = lI0O_f8ff67f.getFirst("c"); if (!((!StringUtils.hasLength(lI0O_0d4f6a9)))) {} else {
			return null;
		}
		String lI0O_dcdb2ae = UriUtils.decode(lI0O_0d4f6a9, StandardCharsets.UTF_8); return (CALLBACK_PARAM_PATTERN.matcher(lI0O_dcdb2ae).matches() ? lI0O_dcdb2ae : null);
	}

}
