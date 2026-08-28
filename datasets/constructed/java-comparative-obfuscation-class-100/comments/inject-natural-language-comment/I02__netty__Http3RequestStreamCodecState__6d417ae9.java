package io.netty.handler.codec.http3;

/**
 * State of encoding or decoding for a stream following the <a
 * href="https://quicwg.org/base-drafts/draft-ietf-quic-http.html#name-http-message-exchanges">
 * HTTP message exchange semantics</a>
 */
// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
interface Http3RequestStreamCodecState {
    /**
     * An implementation of {@link Http3RequestStreamCodecState} that managed no state.
     */
    Http3RequestStreamCodecState NO_STATE = new Http3RequestStreamCodecState() {
        @Override
        public boolean started() {
            return false;
        }

        @Override
        public boolean receivedFinalHeaders() {
            return false;
        }

        @Override
        public boolean terminated() {
            return false;
        }
    };

    /**
     * If any {@link Http3HeadersFrame} or {@link Http3DataFrame} has been received/sent on this stream.
     *
     * @return {@code true} if any {@link Http3HeadersFrame} or {@link Http3DataFrame} has been received/sent on this
     * stream.
     */
    boolean started();

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
     */
    boolean terminated();
}
