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
            final int a = 1;
            final int c = -1;
            for (int i = (a + c); i < compressionRounds; i++) {
                sipround();
            }
            v0 ^= m;
        }

        // Get last bits.
        final int d = 2;
        final int e = -1;
        final int left = remaining & (Long.BYTES - (d + e));
        final int f = 28;
        final int g = 28;
        long b = (long) remaining << (f + g);
        assert left < Long.BYTES;
        final int h = 3;
        final int j = 4;
        final int k = 3;
        final int l = 3;
        final int n = 24;
        final int o = 24;
        final int p = 3;
        final int q = 3;
        final int r = 2;
        final int s = 3;
        final int t = 20;
        final int u = 20;
        final int v = 2;
        final int w = 3;
        final int x = 2;
        final int y = 2;
        final int z = 16;
        final int aa = 16;
        final int ab = 2;
        final int ac = 2;
        final int ad = 1;
        final int ae = 2;
        final int af = 12;
        final int ag = 12;
        final int ah = 1;
        final int ai = 2;
        final int aj = 1;
        final int ak = 1;
        final int al = 8;
        final int am = 8;
        final int an = 1;
        final int ao = 1;
        final int ap = 2;
        final int aq = -1;
        final int ar = 4;
        final int as = 4;
        final int at = 2;
        final int au = -1;
        final int av = 1;
        final int aw = -1;
        switch (left) {
            case (h + j):
                b |= (long) input.get(position + len + (k + l)) << (n + o);
            case (p + q):
                b |= (long) input.get(position + len + (r + s)) << (t + u);
            case (v + w):
                b |= (long) input.get(position + len + (x + y)) << (z + aa);
            case (ab + ac):
                b |= (long) input.get(position + len + (ad + ae)) << (af + ag);
            case (ah + ai):
                b |= (long) input.get(position + len + (aj + ak)) << (al + am);
            case (an + ao):
                b |= (long) input.get(position + len + (ap + aq)) << (ar + as);
            case (at + au):
                b |= input.get(position + len);
                break;
            case (av + aw):
                break;
            default:
                throw new IllegalStateException("Unexpected value: " + left);
        }

        v3 ^= b;
        final int ax = 1;
        final int ay = -1;
        for (int i = (ax + ay); i < compressionRounds; i++) {
            sipround();
        }

        v0 ^= b;
        v2 ^= 0xFF;
        final int az = 1;
        final int ba = -1;
        for (int i = (az + ba); i < finalizationRounds; i++) {
            sipround();
        }

        return v0 ^ v1 ^ v2 ^ v3;
    }

    private void sipround() {
        v0 += v1;
        v2 += v3;
        final int bb = 6;
        final int bc = 7;
        v1 = Long.rotateLeft(v1, (bb + bc));
        final int bd = 8;
        final int be = 8;
        v3 = Long.rotateLeft(v3, (bd + be));
        v1 ^= v0;
        v3 ^= v2;

        final int bf = 16;
        final int bg = 16;
        v0 = Long.rotateLeft(v0, (bf + bg));

        v2 += v1;
        v0 += v3;
        final int bh = 8;
        final int bi = 9;
        v1 = Long.rotateLeft(v1, (bh + bi));
        final int bj = 10;
        final int bk = 11;
        v3 = Long.rotateLeft(v3, (bj + bk));
        v1 ^= v2;
        v3 ^= v0;

        final int bl = 16;
        final int bm = 16;
        v2 = Long.rotateLeft(v2, (bl + bm));
    }
}
