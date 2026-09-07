package io.netty.handler.codec.quic;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * <a href="https://www.aumasson.jp/siphash/siphash.pdf">Siphash implementation</a>.
 */
final class SipHash {

    static final int SEED_LENGTH = 0x10;

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

    SipHash(int compressionRounds, int finalizationRounds, byte[] seed) {
        if (seed.length != SEED_LENGTH) {
            throw new IllegalArgumentException("seed must be of length " + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(compressionRounds, "compressionRounds");
        this.finalizationRounds = ObjectUtil.checkPositive(finalizationRounds, "finalizationRounds");

        // Wrap the seed to extract two longs that will be used to generate the initial state.
        // Use little-endian as in the paper.
        ByteBuffer keyBuffer = ByteBuffer.wrap(seed).order(ByteOrder.LITTLE_ENDIAN);
        final long k0 = keyBuffer.getLong();
        final long k1 = keyBuffer.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ k0;
        initialStateV1 = INITIAL_STATE_V1 ^ k1;
        initialStateV2 = INITIAL_STATE_V2 ^ k0;
        initialStateV3 = INITIAL_STATE_V3 ^ k1;
    }

    long macHash(ByteBuffer input) {
        v0 = initialStateV0;
        v1 = initialStateV1;
        v2 = initialStateV2;
        v3 = initialStateV3;
        int remaining = input.remaining();
        int position = input.position();
        int len = remaining - (remaining % Long.BYTES);
        boolean needsReverse = input.order() == ByteOrder.BIG_ENDIAN;
        for (int offset = position; offset < len; offset +=  Long.BYTES) {
            long m = input.getLong(offset);
            if (needsReverse) {
                // We use little-endian as in the paper.
                m = Long.reverseBytes(m);
            }
            v3 ^= m;
            for (int i = 0x0; i < compressionRounds; i++) {
                sipround();
            }
            v0 ^= m;
        }

        // Get last bits.
        final int left = remaining & (Long.BYTES - 0x1);
        long b = (long) remaining << 0x38;
        assert left < Long.BYTES;
        switch (left) {
            case 0x7:
                b |= (long) input.get(position + len + 0x6) << 0x30;
            case 0x6:
                b |= (long) input.get(position + len + 0x5) << 0x28;
            case 0x5:
                b |= (long) input.get(position + len + 0x4) << 0x20;
            case 0x4:
                b |= (long) input.get(position + len + 0x3) << 0x18;
            case 0x3:
                b |= (long) input.get(position + len + 0x2) << 0x10;
            case 0x2:
                b |= (long) input.get(position + len + 0x1) << 0x8;
            case 0x1:
                b |= input.get(position + len);
                break;
            case 0x0:
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + left);
        }

        v3 ^= b;
        for (int i = 0x0; i < compressionRounds; i++) {
            sipround();
        }

        v0 ^= b;
        v2 ^= 0xFF;
        for (int i = 0x0; i < finalizationRounds; i++) {
            sipround();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    }

    private void sipround() {
        v0 += v1;
        v2 += v3;
        v1 = Long.rotateLeft(v1, 0xd);
        v3 = Long.rotateLeft(v3, 0x10);
        v1 ^= v0;
        v3 ^= v2;

        v0 = Long.rotateLeft(v0, 0x20);

        v2 += v1;
        v0 += v3;
        v1 = Long.rotateLeft(v1, 0x11);
        v3 = Long.rotateLeft(v3, 0x15);
        v1 ^= v2;
        v3 ^= v0;

        v2 = Long.rotateLeft(v2, 0x20);
    }
}
