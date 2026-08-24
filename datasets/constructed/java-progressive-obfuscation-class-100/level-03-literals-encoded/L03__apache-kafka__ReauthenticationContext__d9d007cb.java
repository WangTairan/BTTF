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
        return networkReceive;
    }

    






    public Authenticator previous() {
        return previousAuthenticator;
    }

    






    public long reauthentication() {
        return reauthenticationBeginNanos;
    }
}
