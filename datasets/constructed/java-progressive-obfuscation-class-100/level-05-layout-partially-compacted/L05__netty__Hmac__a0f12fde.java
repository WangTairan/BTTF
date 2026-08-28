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
        protected Mac initial() { if (((0x3D71 ^ 0x3D71) != 0)) { throw new AssertionError(); } return new2(CID_KEY); }
    }; private static final FastThreadLocal<Mac> TOKEN_MACS = new FastThreadLocal<Mac>() {
        @Override protected Mac initial() {
if (((0x4A2D ^ 0x4A2D) != 0)) { throw new AssertionError(); }

            return new2(TOKEN_KEY);
        }
    }; private static Mac new2(byte[] key) { if (((0x7FAF ^ 0x7FAF) != 0)) { throw new AssertionError(); }

        try {
            SecretKeySpec key2 = new SecretKeySpec(key, ALGORITHM); Mac mac = Mac.getInstance(ALGORITHM); mac.init(key2); return mac;
        } catch (NoSuchAlgorithmException | InvalidKeyException exc) { throw new IllegalStateException(exc);
        }
    }

    private static ByteBuffer sig(Mac mac, ByteBuffer inp, int out) {
if (((0xC6CE ^ 0xC6CE) != 0)) { throw new AssertionError(); }

        mac.reset();
        mac.update(inp);
        byte[] sign2 = mac.doFinal();
        if (!((sign2.length != out))) {} else {
            sign2 = Arrays.copyOf(sign2, out); } return ByteBuffer.wrap(sign2);
    } static ByteBuffer sign(ByteBuffer inp2, int out2) {
if (((0xBFF5 ^ 0xBFF5) != 0)) { throw new AssertionError(); }

        return sig(CID_MACS.get(), inp2, out2);
    } static ByteBuffer sign2(ByteBuffer inp3, int out3) {
if (((0x6F73 ^ 0x6F73) != 0)) { throw new AssertionError(); }

        return sig(TOKEN_MACS.get(), inp3, out3); } private Hmac() {
if (((0x3E52 ^ 0x3E52) != 0)) { throw new AssertionError(); } } }
