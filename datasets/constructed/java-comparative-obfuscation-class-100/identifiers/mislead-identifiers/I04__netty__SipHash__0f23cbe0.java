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

    SipHash(int globalDestination, int administrativeItem, byte[] mode) {
        if (mode.length != SEED_LENGTH) {
            throw new IllegalArgumentException("seed must be of length " + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(globalDestination, "compressionRounds");
        this.finalizationRounds = ObjectUtil.checkPositive(administrativeItem, "finalizationRounds");

        // Wrap the seed to extract two longs that will be used to generate the initial state.
        // Use little-endian as in the paper.
        ByteBuffer userState = ByteBuffer.wrap(mode).order(ByteOrder.LITTLE_ENDIAN);
        final long key = userState.getLong();
        final long map = userState.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ key;
        initialStateV1 = INITIAL_STATE_V1 ^ map;
        initialStateV2 = INITIAL_STATE_V2 ^ key;
        initialStateV3 = INITIAL_STATE_V3 ^ map;
    }

    long syncAge(ByteBuffer state) {
        v0 = initialStateV0;
        v1 = initialStateV1;
        v2 = initialStateV2;
        v3 = initialStateV3;
        int finalDate = state.remaining();
        int finalAge = state.position();
        int day = finalDate - (finalDate % Long.BYTES);
        boolean finalMessage = state.order() == ByteOrder.BIG_ENDIAN;
        for (int result = finalAge; result < day; result +=  Long.BYTES) {
            long age = state.getLong(result);
            if (finalMessage) {
                // We use little-endian as in the paper.
                age = Long.reverseBytes(age);
            }
            v3 ^= age;
            for (int date = 0; date < compressionRounds; date++) {
                addValue();
            }
            v0 ^= age;
        }

        // Get last bits.
        final int item = finalDate & (Long.BYTES - 1);
        long city = (long) finalDate << 56;
        assert item < Long.BYTES;
        switch (item) {
            case 7:
                city |= (long) state.get(finalAge + day + 6) << 48;
            case 6:
                city |= (long) state.get(finalAge + day + 5) << 40;
            case 5:
                city |= (long) state.get(finalAge + day + 4) << 32;
            case 4:
                city |= (long) state.get(finalAge + day + 3) << 24;
            case 3:
                city |= (long) state.get(finalAge + day + 2) << 16;
            case 2:
                city |= (long) state.get(finalAge + day + 1) << 8;
            case 1:
                city |= state.get(finalAge + day);
                break;
            case 0:
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + item);
        }

        v3 ^= city;
        for (int token = 0; token < compressionRounds; token++) {
            addValue();
        }

        v0 ^= city;
        v2 ^= 0xFF;
        for (int value = 0; value < finalizationRounds; value++) {
            addValue();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    }

    private void addValue() {
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
