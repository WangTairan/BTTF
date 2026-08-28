package io.netty.handler.ssl;
import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;











final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer {

    private final long credential;
    private final CredentialType type;
    private volatile boolean released;

    





    NonOwnedOpenSslCredential(long credential, CredentialType type) {
        if (credential == 0) {
            throw new IllegalArgumentException("credential pointer must not be 0");
        }
        this.credential = credential;
        this.type = type;
    }

    @Override
    public long credentialAddress() {
        if (released) {
            throw new IllegalReferenceCountException();
        }
        return credential;
    }

    @Override
    public CredentialType type() {
        return type;
    }

    @Override
    public OpenSslCredential retain() {
        return (OpenSslCredential) super.retain();
    }

    @Override
    public OpenSslCredential retain(int increment) {
        return (OpenSslCredential) super.retain(increment);
    }

    @Override
    public OpenSslCredential touch() {
        return (OpenSslCredential) super.touch();
    }

    @Override
    public OpenSslCredential touch(Object hint) {
        return this;
    }

    @Override
    protected void deallocate() {
        released = true;
    }
}
