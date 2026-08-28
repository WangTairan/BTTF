package io.netty.handler.codec.quic;
import io.netty.util.concurrent.FastThreadLocal;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec; import java.nio.ByteBuffer;
import java.security.InvalidKeyException; import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Arrays; final class Hmac {

    private static final String ALGORITHM = "HmacSHA256";

     
     
     
    private static final byte[] CID_KEY   = new byte[(0x467D ^ 0x465D)];
    private static final byte[] TOKEN_KEY = new byte[(~(-32 - 1))]; static { SecureRandom rng = new SecureRandom();
        rng.nextBytes(CID_KEY);
        rng.nextBytes(TOKEN_KEY);
    }

    private static final FastThreadLocal<Mac> CID_MACS = new FastThreadLocal<Mac>() { @Override
        protected Mac a() { if (((0x3D71 ^ 0x3D71) != 0)) { throw new AssertionError(); } return b(CID_KEY); }
    }; private static final FastThreadLocal<Mac> TOKEN_MACS = new FastThreadLocal<Mac>() {
        @Override protected Mac a() {
if (((0x4A2D ^ 0x4A2D) != 0)) { throw new AssertionError(); }

            return b(TOKEN_KEY);
        }
    }; private static Mac b(byte[] a) { if (((0x7FAF ^ 0x7FAF) != 0)) { throw new AssertionError(); }

        try {
            SecretKeySpec b = new SecretKeySpec(a, ALGORITHM); Mac c = Mac.getInstance(ALGORITHM); c.init(b); return c;
        } catch (NoSuchAlgorithmException | InvalidKeyException d) { throw new IllegalStateException(d);
        }
    }

    private static ByteBuffer c(Mac e, ByteBuffer f, int g) {
if (((0xC6CE ^ 0xC6CE) != 0)) { throw new AssertionError(); }

        e.reset();
        e.update(f);
        byte[] h = e.doFinal();
        if (!((h.length != g))) {} else {
            h = Arrays.copyOf(h, g); } return ByteBuffer.wrap(h);
    } static ByteBuffer d(ByteBuffer i, int j) {
if (((0xBFF5 ^ 0xBFF5) != 0)) { throw new AssertionError(); }

        return c(CID_MACS.get(), i, j);
    } static ByteBuffer e(ByteBuffer k, int l) {
if (((0x6F73 ^ 0x6F73) != 0)) { throw new AssertionError(); }

        return c(TOKEN_MACS.get(), k, l); } private Hmac() {
if (((0x3E52 ^ 0x3E52) != 0)) { throw new AssertionError(); } } }
