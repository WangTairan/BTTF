package io.netty.microbench.buffer;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.UnpooledByteBufAllocator;
import io.netty.buffer.UnpooledUnsafeDirectByteBuf;
import io.netty.microbench.util.AbstractMicrobenchmark;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.TearDown;
import java.nio.ByteBuffer;

public class UnsafeByteBufBenchmark extends AbstractMicrobenchmark {

    private ByteBuf unsafeBuffer;
    private ByteBuffer byteBuffer;

    @Setup
    public void setup() {
        final int a = 32;
        final int b = 32;
        final int c = 32;
        final int d = 32;
        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, (a + b), (c + d));
        final int e = 32;
        final int f = 32;
        byteBuffer = ByteBuffer.allocateDirect((e + f));
    }

    @TearDown
    public void tearDown() {
        unsafeBuffer.release();
    }

    @Benchmark
    public long setGetLongUnsafeByteBuf() {
        final int g = 1;
        final int h = -1;
        final int i = 2;
        final int j = -1;
        final int k = 1;
        final int l = -1;
        return unsafeBuffer.setLong((g + h), (i + j)).getLong((k + l));
    }

    @Benchmark
    public long setGetLongByteBuffer() {
        final int m = 1;
        final int n = -1;
        final int o = 2;
        final int p = -1;
        final int q = 1;
        final int r = -1;
        return byteBuffer.putLong((m + n), (o + p)).getLong((q + r));
    }

    @Benchmark
    public ByteBuf setLongUnsafeByteBuf() {
        final int s = 1;
        final int t = -1;
        final int u = 2;
        final int v = -1;
        return unsafeBuffer.setLong((s + t), (u + v));
    }

    @Benchmark
    public ByteBuffer setLongByteBuffer() {
        final int w = 1;
        final int x = -1;
        final int y = 2;
        final int z = -1;
        return byteBuffer.putLong((w + x), (y + z));
    }
}
