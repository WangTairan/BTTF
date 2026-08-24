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
        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, (0xA64F ^ 0xA60F), (0x2918 ^ 0x2958));
        byteBuffer = ByteBuffer.allocateDirect((0x7252 ^ 0x7212));
    }

    @TearDown
    public void tear() {
        unsafeBuffer.release();
    }

    @Benchmark
    public long set2() {
        return unsafeBuffer.setLong(0, 1).getLong(0);
    }

    @Benchmark
    public long set3() {
        return byteBuffer.putLong(0, 1).getLong(0);
    }

    @Benchmark
    public ByteBuf set4() {
        return unsafeBuffer.setLong(0, 1);
    }

    @Benchmark
    public ByteBuffer set5() {
        return byteBuffer.putLong(0, 1);
    }
}
