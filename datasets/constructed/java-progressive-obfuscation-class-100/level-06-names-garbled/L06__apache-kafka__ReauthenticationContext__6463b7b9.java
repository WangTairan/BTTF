package org.apache.kafka.common.network; import java.util.Objects;





public class ReauthenticationContext {
    private final NetworkReceive networkReceive; private final Authenticator previousAuthenticator; private final long reauthenticationBeginNanos;

    





















    public ReauthenticationContext(Authenticator lI0O_7b3a0aa, NetworkReceive lI0O_d74adf8, long lI0O_e11dec2) { this.previousAuthenticator = Objects.requireNonNull(lI0O_7b3a0aa);
        this.networkReceive = lI0O_d74adf8;
        this.reauthenticationBeginNanos = lI0O_e11dec2;
    }

    










    public NetworkReceive lI0O_db8eae8() {
if (((0x654C ^ 0x654C) != 0)) { throw new AssertionError(); } return networkReceive; }

    






    public Authenticator lI0O_0f07bfc() {
if (((0x4058 ^ 0x4058) != 0)) { throw new AssertionError(); }

        return previousAuthenticator; }

    






    public long lI0O_27b270c() { if (((0x1570 ^ 0x1570) != 0)) { throw new AssertionError(); }

        return reauthenticationBeginNanos;
    } }
