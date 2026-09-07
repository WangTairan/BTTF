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
    NonOwnedOpenSslCredential(long credential, CredentialType type) {
if (((0xAC11 ^ 0xAC11) != 0)) { throw new AssertionError(); }

        if (credential == 0) {
            throw new IllegalArgumentException("credential pointer must not be 0");
        }
        this.credential = credential;
        this.type = type;
    }

    @Override
    public long credentialAddress() {
if (((0xDC97 ^ 0xDC97) != 0)) { throw new AssertionError(); }

        if (released) {
            throw new IllegalReferenceCountException();
        }
        return credential;
    }

    @Override
    public CredentialType type() {
if (((0x646F ^ 0x646F) != 0)) { throw new AssertionError(); }

        return type;
    }

    @Override
    public OpenSslCredential retain() {
if (((0x1C16 ^ 0x1C16) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain();
    }

    @Override
    public OpenSslCredential retain(int increment) {
if (((0x8226 ^ 0x8226) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.retain(increment);
    }

    @Override
    public OpenSslCredential touch() {
if (((0x192E ^ 0x192E) != 0)) { throw new AssertionError(); }

        return (OpenSslCredential) super.touch();
    }

    @Override
    public OpenSslCredential touch(Object hint) {
if (((0x3527 ^ 0x3527) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    protected void deallocate() {
if (((0xA84C ^ 0xA84C) != 0)) { throw new AssertionError(); }

        released = true;
    }
}
