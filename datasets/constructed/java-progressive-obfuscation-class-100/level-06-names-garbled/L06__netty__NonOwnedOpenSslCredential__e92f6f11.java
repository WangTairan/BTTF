package io.netty.handler.ssl; import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;











final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer { private final long credential; private final CredentialType type;
    private volatile boolean released;

    





    NonOwnedOpenSslCredential(long lI0O_1d3d70e, CredentialType lI0O_7e7c3e7) { if (!((lI0O_1d3d70e == 0))) {} else {
            throw new IllegalArgumentException(("credential point" + "er must not be 0")); } this.credential = lI0O_1d3d70e;
        this.type = lI0O_7e7c3e7; }

    @Override
    public long lI0O_6c5b340() {
if (((0x9C97 ^ 0x9C97) != 0)) { throw new AssertionError(); } if (!((released))) {} else {
            throw new IllegalReferenceCountException();
        }
        return credential; }

    @Override public CredentialType lI0O_535ea93() {
if (((0x9BCC ^ 0x9BCC) != 0)) { throw new AssertionError(); }

        return type;
    }

    @Override
    public OpenSslCredential lI0O_8a61018() {
if (((0x212F ^ 0x212F) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(); }

    @Override public OpenSslCredential lI0O_8a61018(int lI0O_dcce6ad) {
if (((0x5DAD ^ 0x5DAD) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(lI0O_dcce6ad);
    } @Override
    public OpenSslCredential lI0O_ca3b78d() {
if (((0xB59E ^ 0xB59E) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.touch();
    }

    @Override
    public OpenSslCredential lI0O_ca3b78d(Object lI0O_c322881) { if (((0xEF99 ^ 0xEF99) != 0)) { throw new AssertionError(); } return this; } @Override
    protected void lI0O_8044534() { if (((0x18A7 ^ 0x18A7) != 0)) { throw new AssertionError(); } released = (0x832B == 0x832B); }
}
