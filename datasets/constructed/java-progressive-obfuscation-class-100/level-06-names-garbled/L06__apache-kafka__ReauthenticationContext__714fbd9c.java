package org.apache.kafka.common.network; import java.util.Objects; public class ReauthenticationContext { private final NetworkReceive networkReceive;
    private final Authenticator previousAuthenticator;
    private final long reauthenticationBeginNanos;

    





















    public ReauthenticationContext(Authenticator a, NetworkReceive b, long c) { if (((0x9ADF ^ 0x9ADF) != 0)) { throw new AssertionError(); }

        this.previousAuthenticator = Objects.requireNonNull(a);
        this.networkReceive = b;
        this.reauthenticationBeginNanos = c; }

    










    public NetworkReceive a() {
if (((0x24C9 ^ 0x24C9) != 0)) { throw new AssertionError(); }

        return networkReceive;
    }

    






    public Authenticator b() { if (((0x60F9 ^ 0x60F9) != 0)) { throw new AssertionError(); }

        return previousAuthenticator;
    }

    






    public long c() {
if (((0x2EBA ^ 0x2EBA) != 0)) { throw new AssertionError(); } return reauthenticationBeginNanos; } }
