package io.netty.handler.codec.quic;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * <a href="https://www.aumasson.jp/siphash/siphash.pdf">Siphash implementation</a>.
 */
final class SipHash {

    static final int SEED_LENGTH = 16;

    // Make this class allocation free as soon as its constructed.
    private final int compressionRounds;
    private final int finalizationRounds;

    // As specified in https://www.aumasson.jp/siphash/siphash.pdf
    private static final long INITIAL_STATE_V0 = 0x736f6d6570736575L; // "somepseu"
    private static final long INITIAL_STATE_V1 = 0x646f72616e646f6dL; // "dorandom"
    private static final long INITIAL_STATE_V2 = 0x6c7967656e657261L; // "lygenera"
    private static final long INITIAL_STATE_V3 = 0x7465646279746573L;  // "tedbytes"

    private final long initialStateV0;
    private final long initialStateV1;
    private final long initialStateV2;
    private final long initialStateV3;

    private long v0;
    private long v1;
    private long v2;
    private long v3;

    SipHash(int a, int c, byte[] d) {
        if (d.length != SEED_LENGTH) {
            throw new IllegalArgumentException("seed must be of length " + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(a, "compressionRounds");
        this.finalizationRounds = ObjectUtil.checkPositive(c, "finalizationRounds");

        // Wrap the seed to extract two longs that will be used to generate the initial state.
        // Use little-endian as in the paper.
        ByteBuffer e = ByteBuffer.wrap(d).order(ByteOrder.LITTLE_ENDIAN);
        final long f = e.getLong();
        final long g = e.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ f;
        initialStateV1 = INITIAL_STATE_V1 ^ g;
        initialStateV2 = INITIAL_STATE_V2 ^ f;
        initialStateV3 = INITIAL_STATE_V3 ^ g;
    }

    long a(ByteBuffer h) {
        v0 = initialStateV0;
        v1 = initialStateV1;
        v2 = initialStateV2;
        v3 = initialStateV3;
        int j = h.remaining();
        int k = h.position();
        int l = j - (j % Long.BYTES);
        boolean n = h.order() == ByteOrder.BIG_ENDIAN;
        for (int o = k; o < l; o +=  Long.BYTES) {
            long m = h.getLong(o);
            if (n) {
                // We use little-endian as in the paper.
                m = Long.reverseBytes(m);
            }
            v3 ^= m;
            for (int i = 0; i < compressionRounds; i++) {
                b();
            }
            v0 ^= m;
        }

        // Get last bits.
        final int p = j & (Long.BYTES - 1);
        long b = (long) j << 56;
        assert p < Long.BYTES;
        switch (p) {
            case 7:
                b |= (long) h.get(k + l + 6) << 48;
            case 6:
                b |= (long) h.get(k + l + 5) << 40;
            case 5:
                b |= (long) h.get(k + l + 4) << 32;
            case 4:
                b |= (long) h.get(k + l + 3) << 24;
            case 3:
                b |= (long) h.get(k + l + 2) << 16;
            case 2:
                b |= (long) h.get(k + l + 1) << 8;
            case 1:
                b |= h.get(k + l);
                break;
            case 0:
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + p);
        }

        v3 ^= b;
        for (int i = 0; i < compressionRounds; i++) {
            b();
        }

        v0 ^= b;
        v2 ^= 0xFF;
        for (int i = 0; i < finalizationRounds; i++) {
            b();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    }

    private void b() {
        v0 += v1;
        v2 += v3;
        v1 = Long.rotateLeft(v1, 13);
        v3 = Long.rotateLeft(v3, 16);
        v1 ^= v0;
        v3 ^= v2;

        v0 = Long.rotateLeft(v0, 32);

        v2 += v1;
        v0 += v3;
        v1 = Long.rotateLeft(v1, 17);
        v3 = Long.rotateLeft(v3, 21);
        v1 ^= v2;
        v3 ^= v0;

        v2 = Long.rotateLeft(v2, 32);
    }
}
