package io.netty.handler.ssl;
import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;

/**
 * Signs the input with the given key
 * and returns the signed bytes. @param
 * engine the {@link SSLEngine} @param
 * signatureAlgorithm the algorithm to
 * use for signing @param input the digest
 * itself @return the signed data (must
 * not be {@code null}) @throws Exception
 * thrown if an error is encountered during the signing
 */
final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer {

    private final long credential;
    private final CredentialType type;
    private volatile boolean released;

    /**
     * A {@link ByteBuf} implementation
     * that wraps another buffer to prevent
     * a user from increasing or decreasing
     * the wrapped buffer's reference count.
     */
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
