package io.netty.handler.ssl;
import io.netty.internal.tcnative.SSLPrivateKeyMethod;
import io.netty.util.internal.UnstableApi;
import javax.net.ssl.SSLEngine;




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

    








    byte[] sig(SSLEngine eng, int signature, byte[] inp) throws Exception;

    







    byte[] dec(SSLEngine eng2, byte[] inp2) throws Exception;
}
