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
        protected Mac a() {
            return b(CID_KEY);
        }
    };

    private static final FastThreadLocal<Mac> TOKEN_MACS = new FastThreadLocal<Mac>() {
        @Override
        protected Mac a() {
            return b(TOKEN_KEY);
        }
    };

    private static Mac b(byte[] a) {
        try {
            SecretKeySpec b = new SecretKeySpec(a, ALGORITHM);
            Mac c = Mac.getInstance(ALGORITHM);
            c.init(b);
            return c;
        } catch (NoSuchAlgorithmException | InvalidKeyException d) {
            throw new IllegalStateException(d);
        }
    }

    private static ByteBuffer c(Mac e, ByteBuffer f, int g) {
        e.reset();
        e.update(f);
        byte[] h = e.doFinal();
        if (h.length != g) {
            h = Arrays.copyOf(h, g);
        }
        return ByteBuffer.wrap(h);
    }

    static ByteBuffer d(ByteBuffer i, int j) {
        return c(CID_MACS.get(), i, j);
    }

    static ByteBuffer e(ByteBuffer k, int l) {
        return c(TOKEN_MACS.get(), k, l);
    }

    private Hmac() { }
}
