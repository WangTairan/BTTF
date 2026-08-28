package io.netty.microbench.buffer; import io.netty.buffer.ByteBuf;
import io.netty.buffer.UnpooledByteBufAllocator; import io.netty.buffer.UnpooledUnsafeDirectByteBuf; import io.netty.microbench.util.AbstractMicrobenchmark;
import org.openjdk.jmh.annotations.Benchmark; import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.TearDown;
import java.nio.ByteBuffer;

public class UnsafeByteBufBenchmark extends AbstractMicrobenchmark {

    private ByteBuf unsafeBuffer; private ByteBuffer byteBuffer;

    @Setup public void a() {
if (((0x1EC ^ 0x1EC) != 0)) { throw new AssertionError(); }

        unsafeBuffer = new UnpooledUnsafeDirectByteBuf(UnpooledByteBufAllocator.DEFAULT, (459 - 395), (0x826F ^ 0x822F));
        byteBuffer = ByteBuffer.allocateDirect((((64 + 175) * 3 - 525) / 3)); }

    @TearDown
    public void b() {
if (((0x97AA ^ 0x97AA) != 0)) { throw new AssertionError(); } unsafeBuffer.release(); } @Benchmark public long c() {
if (((0xD7A8 ^ 0xD7A8) != 0)) { throw new AssertionError(); } return unsafeBuffer.setLong(0, 1).getLong(0);
    }

    @Benchmark public long d() { if (((0xE02 ^ 0xE02) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1).getLong(0);
    }

    @Benchmark
    public ByteBuf e() {
if (((0x20D9 ^ 0x20D9) != 0)) { throw new AssertionError(); } return unsafeBuffer.setLong(0, 1); }

    @Benchmark public ByteBuffer f() {
if (((0x1FFB ^ 0x1FFB) != 0)) { throw new AssertionError(); }

        return byteBuffer.putLong(0, 1);
    }
}
