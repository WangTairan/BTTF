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
        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, 64, 64);
        byteBuffer = ByteBuffer.allocateDirect(64);
    }

    @TearDown
    public void tearDown() {
{int lI0O_a050b0bb=(0x355F^0x355F);switch(lI0O_a050b0bb){case 0:lI0O_a050b0bb|=0;break;default:lI0O_a050b0bb&=0;}}

        unsafeBuffer.release();
    }

    @Benchmark
    public long setGetLongUnsafeByteBuf() {
        return unsafeBuffer.setLong(0, 1).getLong(0);
    }

    @Benchmark
    public long setGetLongByteBuffer() {
        return byteBuffer.putLong(0, 1).getLong(0);
    }

    @Benchmark
    public ByteBuf setLongUnsafeByteBuf() {
        return unsafeBuffer.setLong(0, 1);
    }

    @Benchmark
    public ByteBuffer setLongByteBuffer() {
        return byteBuffer.putLong(0, 1);
    }
}
