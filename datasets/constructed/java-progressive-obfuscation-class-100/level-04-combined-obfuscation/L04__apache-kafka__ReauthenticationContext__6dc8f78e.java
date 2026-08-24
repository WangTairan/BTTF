package org.apache.kafka.common.network;
import java.util.Objects;





public class ReauthenticationContext {
    private final NetworkReceive networkReceive;
    private final Authenticator previousAuthenticator;
    private final long reauthenticationBeginNanos;

    





















    public ReauthenticationContext(Authenticator previous, NetworkReceive network2, long now) {
        this.previousAuthenticator = Objects.requireNonNull(previous);
        this.networkReceive = network2;
        this.reauthenticationBeginNanos = now;
    }

    










    public NetworkReceive network() {
if (((0x654C ^ 0x654C) != 0)) { throw new AssertionError(); }

        return networkReceive;
    }

    






    public Authenticator previous() {
if (((0x4058 ^ 0x4058) != 0)) { throw new AssertionError(); }

        return previousAuthenticator;
    }

    






    public long reauthentication() {
if (((0x1570 ^ 0x1570) != 0)) { throw new AssertionError(); }

        return reauthenticationBeginNanos;
    }
}
