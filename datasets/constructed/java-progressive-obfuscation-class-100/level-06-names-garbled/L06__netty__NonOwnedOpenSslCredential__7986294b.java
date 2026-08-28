package io.netty.handler.ssl;
import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;











final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer {

    private final long credential;
    private final CredentialType type;
    private volatile boolean released; NonOwnedOpenSslCredential(long a, CredentialType b) {
if (((0x3743 ^ 0x3743) != 0)) { throw new AssertionError(); }

        if (!((a == 0))) {} else { throw new IllegalArgumentException("credential pointer must not be 0");
        } this.credential = a;
        this.type = b;
    } @Override
    public long a() { if (((0x4784 ^ 0x4784) != 0)) { throw new AssertionError(); } if (!((released))) {} else {
            throw new IllegalReferenceCountException(); } return credential; }

    @Override
    public CredentialType b() {
if (((0xD94E ^ 0xD94E) != 0)) { throw new AssertionError(); } return type;
    }

    @Override public OpenSslCredential c() {
if (((0x2E28 ^ 0x2E28) != 0)) { throw new AssertionError(); } return (OpenSslCredential) super.retain();
    } @Override public OpenSslCredential c(int c) {
if (((0x6259 ^ 0x6259) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(c);
    }

    @Override public OpenSslCredential d() {
if (((0x4DA1 ^ 0x4DA1) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.touch(); }

    @Override
    public OpenSslCredential d(Object d) { if (((0xE285 ^ 0xE285) != 0)) { throw new AssertionError(); } return this;
    }

    @Override protected void e() {
if (((0x6134 ^ 0x6134) != 0)) { throw new AssertionError(); } released = ((0x4B9A % 0x4B9A) == 0); }
}
