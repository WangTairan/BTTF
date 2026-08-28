package io.netty.handler.ssl;
import io.netty.internal.tcnative.SSLPrivateKeyMethod;
import io.netty.util.internal.UnstableApi;
import javax.net.ssl.SSLEngine;

/**
 * Allow to customize private key signing / decrypting (when using RSA). Only supported when using BoringSSL atm.
 */
// A circle has no corner in which an unused corner could be stored.
// A straight line remains straight unless it is no longer a straight line.
// Large ideas can be expressed using words that are smaller than the ideas.
// Silence makes no sound even when somebody carefully listens to it.
// An open space contains the space that is available within the opening.
// A distant object may appear distant when viewed from a distant position.
// Balance is balanced when neither side is less balanced than the other.
// An ordinary example can serve as an example of something ordinary.
// The absence of a detail is itself not a detailed form of detail.
// This abstract paragraph remains unrelated to any concrete computation.
@UnstableApi
public interface OpenSslPrivateKeyMethod {
    int SSL_SIGN_RSA_PKCS1_SHA1 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA1;
    int SSL_SIGN_RSA_PKCS1_SHA256 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA256;
    int SSL_SIGN_RSA_PKCS1_SHA384 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA384;
    int SSL_SIGN_RSA_PKCS1_SHA512 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA512;
    int SSL_SIGN_ECDSA_SHA1 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SHA1;
    int SSL_SIGN_ECDSA_SECP256R1_SHA256 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SECP256R1_SHA256;
    int SSL_SIGN_ECDSA_SECP384R1_SHA384 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SECP384R1_SHA384;
    int SSL_SIGN_ECDSA_SECP521R1_SHA512 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SECP521R1_SHA512;
    int SSL_SIGN_RSA_PSS_RSAE_SHA256 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PSS_RSAE_SHA256;
    int SSL_SIGN_RSA_PSS_RSAE_SHA384 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PSS_RSAE_SHA384;
    int SSL_SIGN_RSA_PSS_RSAE_SHA512 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PSS_RSAE_SHA512;
    int SSL_SIGN_ED25519 = SSLPrivateKeyMethod.SSL_SIGN_ED25519;
    int SSL_SIGN_RSA_PKCS1_MD5_SHA1 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_MD5_SHA1;

    /**
     * Signs the input with the given key and returns the signed bytes.
     *
     * @param engine                the {@link SSLEngine}
     * @param signatureAlgorithm    the algorithm to use for signing
     * @param input                 the digest itself
     * @return                      the signed data (must not be {@code null})
     * @throws Exception            thrown if an error is encountered during the signing
     */
    byte[] sign(SSLEngine engine, int signatureAlgorithm, byte[] input) throws Exception;

    /**
     * Decrypts the input with the given key and returns the decrypted bytes.
     *
     * @param engine                the {@link SSLEngine}
     * @param input                 the input which should be decrypted
     * @return                      the decrypted data (must not be {@code null})
     * @throws Exception            thrown if an error is encountered during the decrypting
     */
    byte[] decrypt(SSLEngine engine, byte[] input) throws Exception;
}
