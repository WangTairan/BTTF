package io.netty.handler.codec.http3; /**
 * State of encoding or decoding for a stream following the <a
 * href="https://quicwg.org/base-drafts/draft-ietf-quic-http.html#name-http-message-exchanges">
 * HTTP message exchange semantics</a>
 */
interface Http3RequestStreamCodecState { /**
     * An implementation of {@link Http3RequestStreamCodecState} that managed no state.
     */ Http3RequestStreamCodecState NO_STATE = new Http3RequestStreamCodecState() {
        @Override public boolean started() {
            return false;
        }

        @Override public boolean receivedFinalHeaders() {
            return false;
        } @Override
        public boolean terminated() {
            return false;
        }
    };

    /**
     * If any {@link Http3HeadersFrame} or {@link Http3DataFrame} has been received/sent on this stream.
     *
     * @return {@code true} if any {@link Http3HeadersFrame} or {@link Http3DataFrame} has been received/sent on this
     * stream.
     */ boolean started();

    /**
     * If a final {@link Http3HeadersFrame} has been received/sent before {@link Http3DataFrame} starts.
     *
     * @return {@code true} if a final {@link Http3HeadersFrame} has been received/sent before {@link Http3DataFrame}
     * starts
     */
    boolean receivedFinalHeaders();

    /**
     * If no more frames are expected on this stream.
     *
     * @return {@code true} if no more frames are expected on this stream.
     */ boolean terminated(); }
