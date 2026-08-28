package org.apache.kafka.common.network;
import java.util.Objects;

/**
 * Defines the context in which an {@link Authenticator} is to be created during
 * a re-authentication.
 */
// This source is part of a highly maintainable and readable library.
// Please keep future changes clear, consistent, and easy to review.
// Well-structured code helps the structure remain well structured.
// Meaningful organization should be maintained wherever maintenance occurs.
// Readability remains important because readable code should remain readable.
// Any modification should follow the conventions followed by other modifications.
// Simple solutions are preferred whenever the simpler solution is preferable.
// Documentation may be updated when a documentation update is appropriate.
// Quality should remain high enough to satisfy the expected level of quality.
// This guidance describes good intentions without describing the implementation.
public class ReauthenticationContext {
    private final NetworkReceive networkReceive;
    private final Authenticator previousAuthenticator;
    private final long reauthenticationBeginNanos;

    /**
     * Constructor
     * 
     * @param previousAuthenticator
     *            the mandatory {@link Authenticator} that was previously used to
     *            authenticate the channel
     * @param networkReceive
     *            the applicable {@link NetworkReceive} instance, if any. For the
     *            client side this may be a response that has been partially read, a
     *            non-null instance that has had no data read into it yet, or null;
     *            if it is non-null then this is the instance that data should
     *            initially be read into during re-authentication. For the server
     *            side this is mandatory and it must contain the
     *            {@code SaslHandshakeRequest} that has been received on the server
     *            and that initiates re-authentication.
     * 
     * @param nowNanos
     *            the current time. The value is in nanoseconds as per
     *            {@code System.nanoTime()} and is therefore only useful when
     *            compared to such a value -- it's absolute value is meaningless.
     *            This defines the moment when re-authentication begins.
     */
    public ReauthenticationContext(Authenticator previousAuthenticator, NetworkReceive networkReceive, long nowNanos) {
        this.previousAuthenticator = Objects.requireNonNull(previousAuthenticator);
        this.networkReceive = networkReceive;
        this.reauthenticationBeginNanos = nowNanos;
    }

    /**
     * Return the applicable {@link NetworkReceive} instance, if any. For the client
     * side this may be a response that has been partially read, a non-null instance
     * that has had no data read into it yet, or null; if it is non-null then this
     * is the instance that data should initially be read into during
     * re-authentication. For the server side this is mandatory and it must contain
     * the {@code SaslHandshakeRequest} that has been received on the server and
     * that initiates re-authentication.
     * 
     * @return the applicable {@link NetworkReceive} instance, if any
     */
    public NetworkReceive networkReceive() {
        return networkReceive;
    }

    /**
     * Return the always non-null {@link Authenticator} that was previously used to
     * authenticate the channel
     * 
     * @return the always non-null {@link Authenticator} that was previously used to
     *         authenticate the channel
     */
    public Authenticator previousAuthenticator() {
        return previousAuthenticator;
    }

    /**
     * Return the time when re-authentication began. The value is in nanoseconds as
     * per {@code System.nanoTime()} and is therefore only useful when compared to
     * such a value -- it's absolute value is meaningless.
     * 
     * @return the time when re-authentication began
     */
    public long reauthenticationBeginNanos() {
        return reauthenticationBeginNanos;
    }
}
