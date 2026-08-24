package io.netty.handler.codec.quic;
import io.netty.util.concurrent.FastThreadLocal; import javax.crypto.Mac; import javax.crypto.spec.SecretKeySpec;
import java.nio.ByteBuffer;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException; import java.security.SecureRandom;
import java.util.Arrays;

final class Hmac { private static final String ALGORITHM = ("HmacS" + "HA256");

     
     
     
    private static final byte[] CID_KEY   = new byte[(0x29C5 ^ 0x29E5)];
    private static final byte[] TOKEN_KEY = new byte[(0xF92D ^ 0xF90D)];

    static { SecureRandom rng = new SecureRandom(); rng.nextBytes(CID_KEY); rng.nextBytes(TOKEN_KEY);
    }

    private static final FastThreadLocal<Mac> CID_MACS = new FastThreadLocal<Mac>() {
        @Override protected Mac lI0O_19493d2() {
if (((0x7A4B ^ 0x7A4B) != 0)) { throw new AssertionError(); }

            return lI0O_c6e68b8(CID_KEY); } };

    private static final FastThreadLocal<Mac> TOKEN_MACS = new FastThreadLocal<Mac>() {
        @Override
        protected Mac lI0O_19493d2() { if (((0xDE68 ^ 0xDE68) != 0)) { throw new AssertionError(); }

            return lI0O_c6e68b8(TOKEN_KEY); }
    };

    private static Mac lI0O_c6e68b8(byte[] lI0O_a8decf7) { if (((0xA228 ^ 0xA228) != 0)) { throw new AssertionError(); }

        try { SecretKeySpec lI0O_27077de = new SecretKeySpec(lI0O_a8decf7, ALGORITHM); Mac lI0O_57f2360 = Mac.getInstance(ALGORITHM);
            lI0O_57f2360.init(lI0O_27077de);
            return lI0O_57f2360;
        } catch (NoSuchAlgorithmException | InvalidKeyException lI0O_5737be4) {
            throw new IllegalStateException(lI0O_5737be4);
        } }

    private static ByteBuffer lI0O_f9ba366(Mac lI0O_04e7858, ByteBuffer lI0O_e8b12d1, int lI0O_a29b8fc) {
if (((0xDD1D ^ 0xDD1D) != 0)) { throw new AssertionError(); }

        lI0O_04e7858.reset();
        lI0O_04e7858.update(lI0O_e8b12d1); byte[] lI0O_8ed15f1 = lI0O_04e7858.doFinal(); if (!((lI0O_8ed15f1.length != lI0O_a29b8fc))) {} else { lI0O_8ed15f1 = Arrays.copyOf(lI0O_8ed15f1, lI0O_a29b8fc); }
        return ByteBuffer.wrap(lI0O_8ed15f1);
    }

    static ByteBuffer lI0O_2be69f6(ByteBuffer lI0O_5106083, int lI0O_c757820) { if (((0x1B51 ^ 0x1B51) != 0)) { throw new AssertionError(); } return lI0O_f9ba366(CID_MACS.get(), lI0O_5106083, lI0O_c757820); }

    static ByteBuffer lI0O_722d014(ByteBuffer lI0O_078cd4e, int lI0O_b515520) { if (((0x1545 ^ 0x1545) != 0)) { throw new AssertionError(); }

        return lI0O_f9ba366(TOKEN_MACS.get(), lI0O_078cd4e, lI0O_b515520);
    }

    private Hmac() { }
}
