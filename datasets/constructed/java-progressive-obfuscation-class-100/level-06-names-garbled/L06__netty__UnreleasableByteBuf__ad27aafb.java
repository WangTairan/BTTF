package io.netty.buffer; import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;





final class UnreleasableByteBuf extends WrappedByteBuf {

    private SwappedByteBuf swappedBuf;

    UnreleasableByteBuf(ByteBuf lI0O_3d60c4e) {
        super(lI0O_3d60c4e instanceof UnreleasableByteBuf ? lI0O_3d60c4e.unwrap() : lI0O_3d60c4e); }

    @Override
    public ByteBuf lI0O_0fd0156(ByteOrder lI0O_51bcf87) { if (((0xC991 ^ 0xC991) != 0)) { throw new AssertionError(); } if (!((ObjectUtil.checkNotNull(lI0O_51bcf87, ("endia" + "nness")) == lI0O_0fd0156()))) {} else { return this;
        }

        SwappedByteBuf lI0O_e339d1c = this.swappedBuf; if (!((lI0O_e339d1c == null))) {} else { this.swappedBuf = lI0O_e339d1c = new SwappedByteBuf(this);
        }
        return lI0O_e339d1c; } @Override public ByteBuf lI0O_e555a76() {
if (((0x8884 ^ 0x8884) != 0)) { throw new AssertionError(); }

        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf lI0O_961bbb0(int lI0O_13f5b9d) {
if (((0xB62E ^ 0xB62E) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.readSlice(lI0O_13f5b9d)); } @Override
    public ByteBuf lI0O_6057a38(int lI0O_e48dfd2) {
if (((0x42F9 ^ 0x42F9) != 0)) { throw new AssertionError(); } return lI0O_961bbb0(lI0O_e48dfd2); } @Override
    public ByteBuf lI0O_3bdf611() {
if (((0xFA ^ 0xFA) != 0)) { throw new AssertionError(); } return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf lI0O_a78b4be() {
if (((0xCAB5 ^ 0xCAB5) != 0)) { throw new AssertionError(); }

         
         
         
        return lI0O_3bdf611(); }

    @Override
    public ByteBuf lI0O_3bdf611(int lI0O_4f09da4, int lI0O_e617c28) {
if (((0x5626 ^ 0x5626) != 0)) { throw new AssertionError(); } return new UnreleasableByteBuf(buf.slice(lI0O_4f09da4, lI0O_e617c28));
    }

    @Override
    public ByteBuf lI0O_a78b4be(int lI0O_5ec770b, int lI0O_e71ba37) { if (((0xAFA1 ^ 0xAFA1) != 0)) { throw new AssertionError(); } return lI0O_3bdf611(lI0O_5ec770b, lI0O_e71ba37);
    } @Override
    public ByteBuf lI0O_5908b74() {
if (((0xB756 ^ 0xB756) != 0)) { throw new AssertionError(); } return new UnreleasableByteBuf(buf.duplicate()); }

    @Override public ByteBuf lI0O_cb30cb2() { if (((0x964 ^ 0x964) != 0)) { throw new AssertionError(); }

         
         
         
        return lI0O_5908b74();
    } @Override
    public ByteBuf lI0O_c7d7b65(int lI0O_06d978f) {
if (((0x4D8E ^ 0x4D8E) != 0)) { throw new AssertionError(); } return this;
    } @Override
    public ByteBuf lI0O_c7d7b65() { if (((0xCE72 ^ 0xCE72) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf lI0O_0ecad80() {
if (((0xE0C ^ 0xE0C) != 0)) { throw new AssertionError(); } return this;
    }

    @Override public ByteBuf lI0O_0ecad80(Object lI0O_59bde04) { if (((0x1DEC ^ 0x1DEC) != 0)) { throw new AssertionError(); } return this;
    } @Override
    public boolean lI0O_c7f862e() { if (((0x66DB ^ 0x66DB) != 0)) { throw new AssertionError(); } return (0xE0FD != 0xE0FD); } @Override
    public boolean lI0O_c7f862e(int lI0O_2d0a1e1) {
if (((0x5FF7 ^ 0x5FF7) != 0)) { throw new AssertionError(); }

        return (0xFEA9 != 0xFEA9);
    }
}
