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

    SipHash(int defaultBalance, int pendingAddress, byte[] data) {
        if (data.length != SEED_LENGTH) {
            throw new IllegalArgumentException("seed must be of length " + SEED_LENGTH);
        }
        this.compressionRounds = ObjectUtil.checkPositive(defaultBalance, "compressionRounds");
        this.finalizationRounds = ObjectUtil.checkPositive(pendingAddress, "finalizationRounds");

        // Wrap the seed to extract two longs that will be used to generate the initial state.
        // Use little-endian as in the paper.
        ByteBuffer remoteKey = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        final long key = remoteKey.getLong();
        final long map = remoteKey.getLong();

        initialStateV0 = INITIAL_STATE_V0 ^ key;
        initialStateV1 = INITIAL_STATE_V1 ^ map;
        initialStateV2 = INITIAL_STATE_V2 ^ key;
        initialStateV3 = INITIAL_STATE_V3 ^ map;
    }

    long capture(ByteBuffer state) {
        v0 = initialStateV0;
        v1 = initialStateV1;
        v2 = initialStateV2;
        v3 = initialStateV3;
        int nextOrder = state.remaining();
        int response = state.position();
        int age = nextOrder - (nextOrder % Long.BYTES);
        boolean activeRecord = state.order() == ByteOrder.BIG_ENDIAN;
        for (int config = response; config < age; config +=  Long.BYTES) {
            long user = state.getLong(config);
            if (activeRecord) {
                // We use little-endian as in the paper.
                user = Long.reverseBytes(user);
            }
            v3 ^= user;
            for (int flag = 0; flag < compressionRounds; flag++) {
                sendNode();
            }
            v0 ^= user;
        }

        // Get last bits.
        final int date = nextOrder & (Long.BYTES - 1);
        long mode = (long) nextOrder << 56;
        assert date < Long.BYTES;
        switch (date) {
            case 7:
                mode |= (long) state.get(response + age + 6) << 48;
            case 6:
                mode |= (long) state.get(response + age + 5) << 40;
            case 5:
                mode |= (long) state.get(response + age + 4) << 32;
            case 4:
                mode |= (long) state.get(response + age + 3) << 24;
            case 3:
                mode |= (long) state.get(response + age + 2) << 16;
            case 2:
                mode |= (long) state.get(response + age + 1) << 8;
            case 1:
                mode |= state.get(response + age);
                break;
            case 0:
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + date);
        }

        v3 ^= mode;
        for (int path = 0; path < compressionRounds; path++) {
            sendNode();
        }

        v0 ^= mode;
        v2 ^= 0xFF;
        for (int node = 0; node < finalizationRounds; node++) {
            sendNode();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    }

    private void sendNode() {
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
