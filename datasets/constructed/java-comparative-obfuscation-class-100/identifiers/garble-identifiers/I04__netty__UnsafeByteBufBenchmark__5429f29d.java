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
    public void a() {
        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, 64, 64);
        byteBuffer = ByteBuffer.allocateDirect(64);
    }

    @TearDown
    public void b() {
        unsafeBuffer.release();
    }

    @Benchmark
    public long c() {
        return unsafeBuffer.setLong(0, 1).getLong(0);
    }

    @Benchmark
    public long d() {
        return byteBuffer.putLong(0, 1).getLong(0);
    }

    @Benchmark
    public ByteBuf e() {
        return unsafeBuffer.setLong(0, 1);
    }

    @Benchmark
    public ByteBuffer f() {
        return byteBuffer.putLong(0, 1);
    }
}
