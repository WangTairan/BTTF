package org.apache.kafka.common.network;
import java.util.Objects;





public class ReauthenticationContext {
    private final NetworkReceive networkReceive;
    private final Authenticator previousAuthenticator;
    private final long reauthenticationBeginNanos;

    





















    public ReauthenticationContext(Authenticator previousAuthenticator, NetworkReceive networkReceive, long nowNanos) {
        this.previousAuthenticator = Objects.requireNonNull(previousAuthenticator);
        this.networkReceive = networkReceive;
        this.reauthenticationBeginNanos = nowNanos;
    }

    










    public NetworkReceive networkReceive() {
        return networkReceive;
    }

    






    public Authenticator previousAuthenticator() {
        return previousAuthenticator;
    }

    






    public long reauthenticationBeginNanos() {
        return reauthenticationBeginNanos;
    }
}
