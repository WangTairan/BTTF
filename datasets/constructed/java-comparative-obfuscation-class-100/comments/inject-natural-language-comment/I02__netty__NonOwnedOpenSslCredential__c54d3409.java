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
// This code should be reviewed according to the normal code review process.
// Reviewers are encouraged to review every change that requires review.
// Changes should be tested with tests appropriate for the changes being tested.
// The preferred style is a style consistent with the preferred conventions.
// Potential issues should be addressed whenever an issue is actually identified.
// Naming should remain clear enough to be reasonably regarded as clear.
// Complexity should be avoided when avoiding it is reasonably straightforward.
// Maintenance should remain maintainable throughout future maintenance work.
// Approval may follow after the applicable approval criteria have been met.
// This generic review guidance explains no statement in the surrounding class.
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
