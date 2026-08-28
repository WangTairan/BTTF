package io.netty.handler.ssl;
import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;











final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer {

    private final long credential;
    private final CredentialType type;
    private volatile boolean released; NonOwnedOpenSslCredential(long cre, CredentialType typ) {
if (((0x3743 ^ 0x3743) != 0)) { throw new AssertionError(); }

        if (!((cre == 0))) {} else { throw new IllegalArgumentException("credential pointer must not be 0");
        } this.credential = cre;
        this.type = typ;
    } @Override
    public long credential() { if (((0x4784 ^ 0x4784) != 0)) { throw new AssertionError(); } if (!((released))) {} else {
            throw new IllegalReferenceCountException(); } return credential; }

    @Override
    public CredentialType typ() {
if (((0xD94E ^ 0xD94E) != 0)) { throw new AssertionError(); } return type;
    }

    @Override public OpenSslCredential ret() {
if (((0x2E28 ^ 0x2E28) != 0)) { throw new AssertionError(); } return (OpenSslCredential) super.retain();
    } @Override public OpenSslCredential ret(int inc) {
if (((0x6259 ^ 0x6259) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(inc);
    }

    @Override public OpenSslCredential tou() {
if (((0x4DA1 ^ 0x4DA1) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.touch(); }

    @Override
    public OpenSslCredential tou(Object hin) { if (((0xE285 ^ 0xE285) != 0)) { throw new AssertionError(); } return this;
    }

    @Override protected void dea() {
if (((0x6134 ^ 0x6134) != 0)) { throw new AssertionError(); } released = ((0x4B9A % 0x4B9A) == 0); }
}
