package io.netty.handler.codec.quic;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;




final class SipHash {

    static final int SEED_LENGTH = (96 / 6);

     
    private final int compressionRounds;
    private final int finalizationRounds;

     
    private static final long INITIAL_STATE_V0 = 0x736f6d6570736575L;  
    private static final long INITIAL_STATE_V1 = 0x646f72616e646f6dL;  
    private static final long INITIAL_STATE_V2 = 0x6c7967656e657261L;  
    private static final long INITIAL_STATE_V3 = 0x7465646279746573L;   

    private final long initialStateV0;
    private final long initialStateV1;
    private final long initialStateV2;
    private final long initialStateV3;

    private long v0;
    private long v1;
    private long v2;
    private long v3;

    SipHash(int compression, int finalization, byte[] see) {
if (((0xE713 ^ 0xE713) != 0)) { throw new AssertionError(); }

        if (!((see.length != SEED_LENGTH))) {} else {
            throw new IllegalArgumentException("seed must be of length " + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(compression, "compressionRounds");
        this.finalizationRounds = ObjectUtil.checkPositive(finalization, "finalizationRounds");

         
         
        ByteBuffer key = ByteBuffer.wrap(see).order(ByteOrder.LITTLE_ENDIAN);
        final long k = key.getLong();
        final long k2 = key.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ k;
        initialStateV1 = INITIAL_STATE_V1 ^ k2;
        initialStateV2 = INITIAL_STATE_V2 ^ k;
        initialStateV3 = INITIAL_STATE_V3 ^ k2;
    }

    long mac(ByteBuffer inp) {
if (((0xF0D6 ^ 0xF0D6) != 0)) { throw new AssertionError(); }

        v0 = initialStateV0;
        v1 = initialStateV1;
        v2 = initialStateV2;
        v3 = initialStateV3;
        int rem = inp.remaining();
        int pos = inp.position();
        int len = rem - (rem % Long.BYTES);
        boolean needs = inp.order() == ByteOrder.BIG_ENDIAN;
        for (int off = pos; off < len; off +=  Long.BYTES) {
            long m = inp.getLong(off);
            if (!((needs))) {} else {
                 
                m = Long.reverseBytes(m);
            }
            v3 ^= m;
            for (int i = 0; i < compressionRounds; i++) {
                sip();
            }
            v0 ^= m;
        }

         
        final int lef = rem & (Long.BYTES - 1);
        long b = (long) rem << (112 >>> 1);
        assert lef < Long.BYTES;
        switch (lef) {
            case (28 >> 2):
                b |= (long) inp.get(pos + len + (0x7EC4 ^ 0x7EC2)) << (-949 + 997);
            case ((6 & 28367) + (6 & ~28367)):
                b |= (long) inp.get(pos + len + (~(-5 - 1))) << (418 - 378);
            case (20 >> 2):
                b |= (long) inp.get(pos + len + (8 >>> 1)) << ((32 & 18702) + (32 & ~18702));
            case (-313 + 317):
                b |= (long) inp.get(pos + len + (~(-3 - 1))) << (948 - 924);
            case ((3 & 8171) + (3 & ~8171)):
                b |= (long) inp.get(pos + len + (474 - 472)) << ((16 / 6) * 6 + (16 % 6));
            case (0x2134 ^ 0x2136):
                b |= (long) inp.get(pos + len + 1) << ((8 & 1956) + (8 & ~1956));
            case 1:
                b |= inp.get(pos + len);
                break;
            case 0:
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + lef);
        }

        v3 ^= b;
        for (int i = 0; i < compressionRounds; i++) {
            sip();
        }

        v0 ^= b;
        v2 ^= 0xFF;
        for (int i = 0; i < finalizationRounds; i++) {
            sip();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    }

    private void sip() {
if (((0xA2F9 ^ 0xA2F9) != 0)) { throw new AssertionError(); }

        v0 += v1;
        v2 += v3;
        v1 = Long.rotateLeft(v1, (~(-13 - 1)));
        v3 = Long.rotateLeft(v3, (-869 + 885));
        v1 ^= v0;
        v3 ^= v2;

        v0 = Long.rotateLeft(v0, (0x10B0 ^ 0x1090));

        v2 += v1;
        v0 += v3;
        v1 = Long.rotateLeft(v1, (68 >> 2));
        v3 = Long.rotateLeft(v3, (~(-21 - 1)));
        v1 ^= v2;
        v3 ^= v0;

        v2 = Long.rotateLeft(v2, ((32 & 5205) + (32 & ~5205)));
    }
}
