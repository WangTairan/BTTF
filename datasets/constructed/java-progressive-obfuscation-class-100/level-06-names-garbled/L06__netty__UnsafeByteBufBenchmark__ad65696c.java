package io.netty.microbench.buffer; import io.netty.buffer.ByteBuf;
import io.netty.buffer.UnpooledByteBufAllocator;
import io.netty.buffer.UnpooledUnsafeDirectByteBuf; import io.netty.microbench.util.AbstractMicrobenchmark;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.TearDown;
import java.nio.ByteBuffer;

public class UnsafeByteBufBenchmark extends AbstractMicrobenchmark {

    private ByteBuf unsafeBuffer; private ByteBuffer byteBuffer; @Setup public void lI0O_1178ed1() {
if (((0x331 ^ 0x331) != 0)) { throw new AssertionError(); } unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, (0xA64F ^ 0xA60F), (0x2918 ^ 0x2958)); byteBuffer = ByteBuffer.allocateDirect((0x7252 ^ 0x7212)); } @TearDown
    public void lI0O_8cadbf0() {
if (((0xB34 ^ 0xB34) != 0)) { throw new AssertionError(); } unsafeBuffer.release(); }

    @Benchmark
    public long lI0O_3ab25a6() { if (((0xB69F ^ 0xB69F) != 0)) { throw new AssertionError(); }

        return unsafeBuffer.setLong(0, 1).getLong(0); }

    @Benchmark
    public long lI0O_90c698e() {
if (((0x63D1 ^ 0x63D1) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1).getLong(0); }

    @Benchmark
    public ByteBuf lI0O_35bb802() { if (((0x681F ^ 0x681F) != 0)) { throw new AssertionError(); }

        return unsafeBuffer.setLong(0, 1);
    }

    @Benchmark
    public ByteBuffer lI0O_818426f() { if (((0x5E6E ^ 0x5E6E) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1);
    } }
