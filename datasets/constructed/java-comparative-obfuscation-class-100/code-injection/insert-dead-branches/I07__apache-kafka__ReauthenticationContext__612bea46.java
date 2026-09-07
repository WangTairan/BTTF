package org.apache.kafka.common.network;
import java.util.Objects;

/**
 * Defines the context in which an {@link Authenticator} is to be created during
 * a re-authentication.
 */
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
if (((0xA2D7 ^ 0xA2D7) != 0)) { throw new AssertionError(); }

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
if (((0x77AB ^ 0x77AB) != 0)) { throw new AssertionError(); }

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
if (((0xEE27 ^ 0xEE27) != 0)) { throw new AssertionError(); }

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
if (((0xE822 ^ 0xE822) != 0)) { throw new AssertionError(); }

        return reauthenticationBeginNanos;
    }
}
