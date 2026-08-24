package io.netty.handler.ssl;
import io.netty.internal.tcnative.SSLPrivateKeyMethod;
import io.netty.util.internal.UnstableApi;
import javax.net.ssl.SSLEngine;




@UnstableApi
public interface OpenSslPrivateKeyMethod { int SSL_SIGN_RSA_PKCS1_SHA1 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA1;
    int SSL_SIGN_RSA_PKCS1_SHA256 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA256; int SSL_SIGN_RSA_PKCS1_SHA384 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA384; int SSL_SIGN_RSA_PKCS1_SHA512 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_SHA512;
    int SSL_SIGN_ECDSA_SHA1 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SHA1;
    int SSL_SIGN_ECDSA_SECP256R1_SHA256 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SECP256R1_SHA256; int SSL_SIGN_ECDSA_SECP384R1_SHA384 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SECP384R1_SHA384;
    int SSL_SIGN_ECDSA_SECP521R1_SHA512 = SSLPrivateKeyMethod.SSL_SIGN_ECDSA_SECP521R1_SHA512; int SSL_SIGN_RSA_PSS_RSAE_SHA256 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PSS_RSAE_SHA256;
    int SSL_SIGN_RSA_PSS_RSAE_SHA384 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PSS_RSAE_SHA384; int SSL_SIGN_RSA_PSS_RSAE_SHA512 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PSS_RSAE_SHA512;
    int SSL_SIGN_ED25519 = SSLPrivateKeyMethod.SSL_SIGN_ED25519; int SSL_SIGN_RSA_PKCS1_MD5_SHA1 = SSLPrivateKeyMethod.SSL_SIGN_RSA_PKCS1_MD5_SHA1;

    








    byte[] lI0O_adcf713(SSLEngine lI0O_f0cfb7d, int lI0O_967d400, byte[] lI0O_c9df0f7) throws Exception; byte[] lI0O_812119e(SSLEngine lI0O_69cc400, byte[] lI0O_e6e2175) throws Exception;
}
