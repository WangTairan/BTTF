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

    SipHash(int lI0O_aac9188, int lI0O_d6fe3d1, byte[] lI0O_c161fef) {
        if (!((lI0O_c161fef.length != SEED_LENGTH))) {} else { throw new IllegalArgumentException(("seed must b" + "e of length ") + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(lI0O_aac9188, ("compress" + "ionRounds")); this.finalizationRounds = ObjectUtil.checkPositive(lI0O_d6fe3d1, ("finalizat" + "ionRounds"));

         
         
        ByteBuffer lI0O_ae0703f = ByteBuffer.wrap(lI0O_c161fef).order(ByteOrder.LITTLE_ENDIAN); final long lI0O_0658e2d = lI0O_ae0703f.getLong();
        final long lI0O_772bd23 = lI0O_ae0703f.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ lI0O_0658e2d;
        initialStateV1 = INITIAL_STATE_V1 ^ lI0O_772bd23;
        initialStateV2 = INITIAL_STATE_V2 ^ lI0O_0658e2d;
        initialStateV3 = INITIAL_STATE_V3 ^ lI0O_772bd23; } long lI0O_4c0db8b(ByteBuffer lI0O_d2b06fa) { if (((0xFD08 ^ 0xFD08) != 0)) { throw new AssertionError(); }

        v0 = initialStateV0; v1 = initialStateV1; v2 = initialStateV2;
        v3 = initialStateV3;
        int lI0O_ad3691e = lI0O_d2b06fa.remaining(); int lI0O_76691a1 = lI0O_d2b06fa.position();
        int lI0O_481f345 = lI0O_ad3691e - (lI0O_ad3691e % Long.BYTES);
        boolean lI0O_4740376 = lI0O_d2b06fa.order() == ByteOrder.BIG_ENDIAN;
        for (int lI0O_57d2813 = lI0O_76691a1; lI0O_57d2813 < lI0O_481f345; lI0O_57d2813 +=  Long.BYTES) { long lI0O_ab16394 = lI0O_d2b06fa.getLong(lI0O_57d2813); if (!((lI0O_4740376))) {} else { lI0O_ab16394 = Long.reverseBytes(lI0O_ab16394);
            }
            v3 ^= lI0O_ab16394;
            for (int lI0O_4c8583c = 0; lI0O_4c8583c < compressionRounds; lI0O_4c8583c++) {
                lI0O_2273add(); }
            v0 ^= lI0O_ab16394;
        } final int lI0O_8d0c9da = lI0O_ad3691e & (Long.BYTES - 1); long lI0O_7376e77 = (long) lI0O_ad3691e << (0x5A91 ^ 0x5AA9);
        assert lI0O_8d0c9da < Long.BYTES;
        switch (lI0O_8d0c9da) { case (0x806 ^ 0x801):
                lI0O_7376e77 |= (long) lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345 + (0xC049 ^ 0xC04F)) << (0x66AB ^ 0x669B);
            case (0xAF38 ^ 0xAF3E):
                lI0O_7376e77 |= (long) lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345 + (0xE73B ^ 0xE73E)) << (0x1D6C ^ 0x1D44);
            case (0x2D2F ^ 0x2D2A):
                lI0O_7376e77 |= (long) lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345 + (0xD7BF ^ 0xD7BB)) << (0xDE5B ^ 0xDE7B);
            case (0x9807 ^ 0x9803): lI0O_7376e77 |= (long) lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345 + (0x6A6F ^ 0x6A6C)) << (0xFF07 ^ 0xFF1F); case (0xE54B ^ 0xE548): lI0O_7376e77 |= (long) lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345 + (0x8059 ^ 0x805B)) << (0xBBA3 ^ 0xBBB3);
            case (0x5A76 ^ 0x5A74):
                lI0O_7376e77 |= (long) lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345 + 1) << (0xC784 ^ 0xC78C);
            case 1:
                lI0O_7376e77 |= lI0O_d2b06fa.get(lI0O_76691a1 + lI0O_481f345);
                break;
            case 0:
                break;
            default:
                throw new IllegalStateException(("Unexpecte" + "d value: ") + lI0O_8d0c9da);
        }

        v3 ^= lI0O_7376e77; for (int lI0O_ceade89 = 0; lI0O_ceade89 < compressionRounds; lI0O_ceade89++) {
            lI0O_2273add();
        }

        v0 ^= lI0O_7376e77;
        v2 ^= 0xFF;
        for (int lI0O_619f602 = 0; lI0O_619f602 < finalizationRounds; lI0O_619f602++) { lI0O_2273add();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    } private void lI0O_2273add() { if (((0x825C ^ 0x825C) != 0)) { throw new AssertionError(); } v0 += v1;
        v2 += v3; v1 = Long.rotateLeft(v1, (0x4E16 ^ 0x4E1B));
        v3 = Long.rotateLeft(v3, (0xFEBF ^ 0xFEAF));
        v1 ^= v0;
        v3 ^= v2; v0 = Long.rotateLeft(v0, (0x80F7 ^ 0x80D7)); v2 += v1; v0 += v3; v1 = Long.rotateLeft(v1, (0xEA23 ^ 0xEA32)); v3 = Long.rotateLeft(v3, (0x6547 ^ 0x6552));
        v1 ^= v2; v3 ^= v0;

        v2 = Long.rotateLeft(v2, (0x8DC3 ^ 0x8DE3)); } }
