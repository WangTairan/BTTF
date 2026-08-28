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
if (((0x1EC ^ 0x1EC) != 0)) { throw new AssertionError(); }

        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, 64, 64);
        byteBuffer = ByteBuffer.allocateDirect(64);
    }

    @TearDown
    public void tearDown() {
if (((0xCE00 ^ 0xCE00) != 0)) { throw new AssertionError(); }

        unsafeBuffer.release();
    }

    @Benchmark
    public long setGetLongUnsafeByteBuf() {
if (((0x80BD ^ 0x80BD) != 0)) { throw new AssertionError(); }

        return unsafeBuffer.setLong(0, 1).getLong(0);
    }

    @Benchmark
    public long setGetLongByteBuffer() {
if (((0x53F3 ^ 0x53F3) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1).getLong(0);
    }

    @Benchmark
    public ByteBuf setLongUnsafeByteBuf() {
if (((0xC12C ^ 0xC12C) != 0)) { throw new AssertionError(); }

        return unsafeBuffer.setLong(0, 1);
    }

    @Benchmark
    public ByteBuffer setLongByteBuffer() {
if (((0x3C7F ^ 0x3C7F) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1);
    }
}
