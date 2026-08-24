package io.netty.handler.ssl; import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;











final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer { private final long credential; private final CredentialType type;
    private volatile boolean released;

    





    NonOwnedOpenSslCredential(long cre, CredentialType typ) { if (!((cre == 0))) {} else {
            throw new IllegalArgumentException(("credential point" + "er must not be 0")); } this.credential = cre;
        this.type = typ; }

    @Override
    public long credential() {
if (((0x9C97 ^ 0x9C97) != 0)) { throw new AssertionError(); } if (!((released))) {} else {
            throw new IllegalReferenceCountException();
        }
        return credential; }

    @Override public CredentialType typ() {
if (((0x9BCC ^ 0x9BCC) != 0)) { throw new AssertionError(); }

        return type;
    }

    @Override
    public OpenSslCredential ret() {
if (((0x212F ^ 0x212F) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(); }

    @Override public OpenSslCredential ret(int inc) {
if (((0x5DAD ^ 0x5DAD) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(inc);
    } @Override
    public OpenSslCredential tou() {
if (((0xB59E ^ 0xB59E) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.touch();
    }

    @Override
    public OpenSslCredential tou(Object hin) { if (((0xEF99 ^ 0xEF99) != 0)) { throw new AssertionError(); } return this; } @Override
    protected void dea() { if (((0x18A7 ^ 0x18A7) != 0)) { throw new AssertionError(); } released = (0x832B == 0x832B); }
}
