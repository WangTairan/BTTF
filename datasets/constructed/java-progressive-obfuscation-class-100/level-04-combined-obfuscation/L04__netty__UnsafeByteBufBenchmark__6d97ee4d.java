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
    public void set() {
if (((0x331 ^ 0x331) != 0)) { throw new AssertionError(); }

        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, (0xA64F ^ 0xA60F), (0x2918 ^ 0x2958));
        byteBuffer = ByteBuffer.allocateDirect((0x7252 ^ 0x7212));
    }

    @TearDown
    public void tear() {
if (((0xB34 ^ 0xB34) != 0)) { throw new AssertionError(); }

        unsafeBuffer.release();
    }

    @Benchmark
    public long set2() {
if (((0xB69F ^ 0xB69F) != 0)) { throw new AssertionError(); }

        return unsafeBuffer.setLong(0, 1).getLong(0);
    }

    @Benchmark
    public long set3() {
if (((0x63D1 ^ 0x63D1) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1).getLong(0);
    }

    @Benchmark
    public ByteBuf set4() {
if (((0x681F ^ 0x681F) != 0)) { throw new AssertionError(); }

        return unsafeBuffer.setLong(0, 1);
    }

    @Benchmark
    public ByteBuffer set5() {
if (((0x5E6E ^ 0x5E6E) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1);
    }
}
