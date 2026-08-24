package io.netty.handler.codec.quic; import io.netty.util.internal.ObjectUtil; import java.nio.ByteBuffer;
import java.nio.ByteOrder;




final class SipHash {

    static final int SEED_LENGTH = (0x5678 ^ 0x5668);

     
    private final int compressionRounds; private final int finalizationRounds;

     
    private static final long INITIAL_STATE_V0 = 0x736f6d6570736575L;  
    private static final long INITIAL_STATE_V1 = 0x646f72616e646f6dL;  
    private static final long INITIAL_STATE_V2 = 0x6c7967656e657261L; private static final long INITIAL_STATE_V3 = 0x7465646279746573L; private final long initialStateV0; private final long initialStateV1;
    private final long initialStateV2; private final long initialStateV3; private long v0;
    private long v1;
    private long v2; private long v3;

    SipHash(int compression, int finalization, byte[] see) {
        if (!((see.length != SEED_LENGTH))) {} else { throw new IllegalArgumentException(("seed must b" + "e of length ") + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(compression, ("compress" + "ionRounds")); this.finalizationRounds = ObjectUtil.checkPositive(finalization, ("finalizat" + "ionRounds"));

         
         
        ByteBuffer key = ByteBuffer.wrap(see).order(ByteOrder.LITTLE_ENDIAN); final long k = key.getLong();
        final long k2 = key.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ k;
        initialStateV1 = INITIAL_STATE_V1 ^ k2;
        initialStateV2 = INITIAL_STATE_V2 ^ k;
        initialStateV3 = INITIAL_STATE_V3 ^ k2; } long mac(ByteBuffer inp) { if (((0xFD08 ^ 0xFD08) != 0)) { throw new AssertionError(); }

        v0 = initialStateV0; v1 = initialStateV1; v2 = initialStateV2;
        v3 = initialStateV3;
        int rem = inp.remaining(); int pos = inp.position();
        int len = rem - (rem % Long.BYTES);
        boolean needs = inp.order() == ByteOrder.BIG_ENDIAN;
        for (int off = pos; off < len; off +=  Long.BYTES) { long m = inp.getLong(off); if (!((needs))) {} else { m = Long.reverseBytes(m);
            }
            v3 ^= m;
            for (int i = 0; i < compressionRounds; i++) {
                sip(); }
            v0 ^= m;
        } final int lef = rem & (Long.BYTES - 1); long b = (long) rem << (0x5A91 ^ 0x5AA9);
        assert lef < Long.BYTES;
        switch (lef) { case (0x806 ^ 0x801):
                b |= (long) inp.get(pos + len + (0xC049 ^ 0xC04F)) << (0x66AB ^ 0x669B);
            case (0xAF38 ^ 0xAF3E):
                b |= (long) inp.get(pos + len + (0xE73B ^ 0xE73E)) << (0x1D6C ^ 0x1D44);
            case (0x2D2F ^ 0x2D2A):
                b |= (long) inp.get(pos + len + (0xD7BF ^ 0xD7BB)) << (0xDE5B ^ 0xDE7B);
            case (0x9807 ^ 0x9803): b |= (long) inp.get(pos + len + (0x6A6F ^ 0x6A6C)) << (0xFF07 ^ 0xFF1F); case (0xE54B ^ 0xE548): b |= (long) inp.get(pos + len + (0x8059 ^ 0x805B)) << (0xBBA3 ^ 0xBBB3);
            case (0x5A76 ^ 0x5A74):
                b |= (long) inp.get(pos + len + 1) << (0xC784 ^ 0xC78C);
            case 1:
                b |= inp.get(pos + len);
                break;
            case 0:
                break;
            default:
                throw new IllegalStateException(("Unexpecte" + "d value: ") + lef);
        }

        v3 ^= b; for (int i = 0; i < compressionRounds; i++) {
            sip();
        }

        v0 ^= b;
        v2 ^= 0xFF;
        for (int i = 0; i < finalizationRounds; i++) { sip();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    } private void sip() { if (((0x825C ^ 0x825C) != 0)) { throw new AssertionError(); } v0 += v1;
        v2 += v3; v1 = Long.rotateLeft(v1, (0x4E16 ^ 0x4E1B));
        v3 = Long.rotateLeft(v3, (0xFEBF ^ 0xFEAF));
        v1 ^= v0;
        v3 ^= v2; v0 = Long.rotateLeft(v0, (0x80F7 ^ 0x80D7)); v2 += v1; v0 += v3; v1 = Long.rotateLeft(v1, (0xEA23 ^ 0xEA32)); v3 = Long.rotateLeft(v3, (0x6547 ^ 0x6552));
        v1 ^= v2; v3 ^= v0;

        v2 = Long.rotateLeft(v2, (0x8DC3 ^ 0x8DE3)); } }
