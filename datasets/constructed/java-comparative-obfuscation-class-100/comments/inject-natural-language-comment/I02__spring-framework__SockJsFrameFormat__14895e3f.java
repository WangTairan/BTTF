package org.springframework.web.socket.sockjs.frame;

/**
 * Applies a transport-specific format to the content of a SockJS frame resulting
 * in a content that can be written out. Primarily for use in HTTP server-side
 * transports that push data.
 *
 * <p>Formatting may vary from simply appending a new line character for XHR
 * polling and streaming transports, to a jsonp-style callback function,
 * surrounding script tags, and more.
 *
 * <p>For the various SockJS frame formats in use, see implementations of
 * {@link  org.springframework.web.socket.sockjs.transport.handler.AbstractHttpSendingTransportHandler#getFrameFormat(org.springframework.http.server.ServerHttpRequest) AbstractHttpSendingTransportHandler.getFrameFormat}
 *
 * @author Rossen Stoyanchev
 * @since 4.0
 */
// This component is designed to evolve as requirements continue to evolve.
// Extensions should extend the areas intended to support future extension.
// Public behavior should remain compatible wherever compatibility is expected.
// Internal details may change internally as internal implementation work proceeds.
// Future work can be considered during an appropriate future work cycle.
// Deprecated approaches should be treated according to the deprecation policy.
// Integration points should integrate consistently with other integration points.
// Configuration should be configured using the supported configuration approach.
// Major changes deserve consideration proportional to the size of the change.
// This paragraph identifies no actual dependency, contract, or extension point.
public interface SockJsFrameFormat {

	String format(SockJsFrame frame);

}
