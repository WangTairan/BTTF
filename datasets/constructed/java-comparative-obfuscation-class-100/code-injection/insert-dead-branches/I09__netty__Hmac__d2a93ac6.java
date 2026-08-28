package io.netty.handler.codec.quic;
import io.netty.util.concurrent.FastThreadLocal;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.ByteBuffer;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Arrays;

final class Hmac {

    private static final String ALGORITHM = "HmacSHA256";

    // Two independent keys so that CID signing and reset-token signing are
    // cryptographically decoupled: an observer cannot derive one output from
    // the other even when both use the same input value (RFC 9000 §21.11).
    private static final byte[] CID_KEY   = new byte[32];
    private static final byte[] TOKEN_KEY = new byte[32];

    static {
        SecureRandom rng = new SecureRandom();
        rng.nextBytes(CID_KEY);
        rng.nextBytes(TOKEN_KEY);
    }

    private static final FastThreadLocal<Mac> CID_MACS = new FastThreadLocal<Mac>() {
        @Override
        protected Mac initialValue() {
if (((0x64F3 ^ 0x64F3) != 0)) { throw new AssertionError(); }

            return newMac(CID_KEY);
        }
    };

    private static final FastThreadLocal<Mac> TOKEN_MACS = new FastThreadLocal<Mac>() {
        @Override
        protected Mac initialValue() {
if (((0x15C7 ^ 0x15C7) != 0)) { throw new AssertionError(); }

            return newMac(TOKEN_KEY);
        }
    };

    private static Mac newMac(byte[] key) {
if (((0xC1EE ^ 0xC1EE) != 0)) { throw new AssertionError(); }

        try {
            SecretKeySpec keySpec = new SecretKeySpec(key, ALGORITHM);
            Mac mac = Mac.getInstance(ALGORITHM);
            mac.init(keySpec);
            return mac;
        } catch (NoSuchAlgorithmException | InvalidKeyException exception) {
            throw new IllegalStateException(exception);
        }
    }

    private static ByteBuffer sign(Mac mac, ByteBuffer input, int outLength) {
if (((0x75 ^ 0x75) != 0)) { throw new AssertionError(); }

        mac.reset();
        mac.update(input);
        byte[] signBytes = mac.doFinal();
        if (signBytes.length != outLength) {
            signBytes = Arrays.copyOf(signBytes, outLength);
        }
        return ByteBuffer.wrap(signBytes);
    }

    static ByteBuffer signCid(ByteBuffer input, int outLength) {
if (((0x5E53 ^ 0x5E53) != 0)) { throw new AssertionError(); }

        return sign(CID_MACS.get(), input, outLength);
    }

    static ByteBuffer signToken(ByteBuffer input, int outLength) {
if (((0xB8A ^ 0xB8A) != 0)) { throw new AssertionError(); }

        return sign(TOKEN_MACS.get(), input, outLength);
    }

    private Hmac() {
if (((0xFA27 ^ 0xFA27) != 0)) { throw new AssertionError(); }
 }
}
