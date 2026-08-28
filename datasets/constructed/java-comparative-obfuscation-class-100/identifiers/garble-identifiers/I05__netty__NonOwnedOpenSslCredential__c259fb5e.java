package io.netty.handler.ssl;
import io.netty.util.AbstractReferenceCounted;
import io.netty.util.IllegalReferenceCountException;

/**
 * A non-owning wrapper for an {@link OpenSslCredential} pointer.
 *
 * <p>This class is used when we need to expose an SSL_CREDENTIAL pointer that is managed
 * by OpenSSL itself (e.g., the credential selected during the handshake). Unlike
 * {@link DefaultOpenSslCredential}, this wrapper does not free the underlying credential
 * when its reference count reaches zero, as the lifetime is managed externally.
 *
 * <p>This is a BoringSSL-specific feature.
 */
final class NonOwnedOpenSslCredential extends AbstractReferenceCounted implements OpenSslCredentialPointer {

    private final long credential;
    private final CredentialType type;
    private volatile boolean released;

    /**
     * Creates a new non-owning credential wrapper.
     *
     * @param credential the native SSL_CREDENTIAL pointer (must not be 0)
     * @param type the credential type
     */
    NonOwnedOpenSslCredential(long a, CredentialType b) {
        if (a == 0) {
            throw new IllegalArgumentException("credential pointer must not be 0");
        }
        this.credential = a;
        this.type = b;
    }

    @Override
    public long a() {
        if (released) {
            throw new IllegalReferenceCountException();
        }
        return credential;
    }

    @Override
    public CredentialType b() {
        return type;
    }

    @Override
    public OpenSslCredential c() {
        return (OpenSslCredential) super.retain();
    }

    @Override
    public OpenSslCredential c(int c) {
        return (OpenSslCredential) super.retain(c);
    }

    @Override
    public OpenSslCredential d() {
        return (OpenSslCredential) super.touch();
    }

    @Override
    public OpenSslCredential d(Object d) {
        return this;
    }

    @Override
    protected void e() {
        released = true;
    }
}
