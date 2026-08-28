package org.apache.kafka.common.network; import java.util.Objects; public class ReauthenticationContext { private final NetworkReceive networkReceive;
    private final Authenticator previousAuthenticator;
    private final long reauthenticationBeginNanos;

    





















    public ReauthenticationContext(Authenticator previous, NetworkReceive network2, long now) { if (((0x9ADF ^ 0x9ADF) != 0)) { throw new AssertionError(); }

        this.previousAuthenticator = Objects.requireNonNull(previous);
        this.networkReceive = network2;
        this.reauthenticationBeginNanos = now; }

    










    public NetworkReceive network() {
if (((0x24C9 ^ 0x24C9) != 0)) { throw new AssertionError(); }

        return networkReceive;
    }

    






    public Authenticator previous() { if (((0x60F9 ^ 0x60F9) != 0)) { throw new AssertionError(); }

        return previousAuthenticator;
    }

    






    public long reauthentication() {
if (((0x2EBA ^ 0x2EBA) != 0)) { throw new AssertionError(); } return reauthenticationBeginNanos; } }
