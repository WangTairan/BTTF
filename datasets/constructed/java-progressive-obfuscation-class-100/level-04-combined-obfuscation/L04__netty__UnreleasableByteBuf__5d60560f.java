package io.netty.buffer;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;





final class UnreleasableByteBuf extends WrappedByteBuf {

    private SwappedByteBuf swappedBuf;

    UnreleasableByteBuf(ByteBuf buf) {
        super(buf instanceof UnreleasableByteBuf ? buf.unwrap() : buf);
    }

    @Override
    public ByteBuf ord(ByteOrder end) {
if (((0xC991 ^ 0xC991) != 0)) { throw new AssertionError(); }

        if (!((ObjectUtil.checkNotNull(end, ("endia" + "nness")) == ord()))) {} else {
            return this;
        }

        SwappedByteBuf swapped = this.swappedBuf;
        if (!((swapped == null))) {} else {
            this.swappedBuf = swapped = new SwappedByteBuf(this);
        }
        return swapped;
    }

    @Override
    public ByteBuf as() {
if (((0x8884 ^ 0x8884) != 0)) { throw new AssertionError(); }

        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf read(int len) {
if (((0xB62E ^ 0xB62E) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.readSlice(len));
    }

    @Override
    public ByteBuf read2(int len2) {
if (((0x42F9 ^ 0x42F9) != 0)) { throw new AssertionError(); }

         
         
         
        return read(len2);
    }

    @Override
    public ByteBuf sli() {
if (((0xFA ^ 0xFA) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf retained() {
if (((0xCAB5 ^ 0xCAB5) != 0)) { throw new AssertionError(); }

         
         
         
        return sli();
    }

    @Override
    public ByteBuf sli(int ind, int len3) {
if (((0x5626 ^ 0x5626) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice(ind, len3));
    }

    @Override
    public ByteBuf retained(int ind2, int len4) {
if (((0xAFA1 ^ 0xAFA1) != 0)) { throw new AssertionError(); }

         
         
         
        return sli(ind2, len4);
    }

    @Override
    public ByteBuf dup() {
if (((0xB756 ^ 0xB756) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf retained2() {
if (((0x964 ^ 0x964) != 0)) { throw new AssertionError(); }

         
         
         
        return dup();
    }

    @Override
    public ByteBuf ret(int inc) {
if (((0x4D8E ^ 0x4D8E) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf ret() {
if (((0xCE72 ^ 0xCE72) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf tou() {
if (((0xE0C ^ 0xE0C) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf tou(Object hin) {
if (((0x1DEC ^ 0x1DEC) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public boolean rel() {
if (((0x66DB ^ 0x66DB) != 0)) { throw new AssertionError(); }

        return (0xE0FD != 0xE0FD);
    }

    @Override
    public boolean rel(int dec) {
if (((0x5FF7 ^ 0x5FF7) != 0)) { throw new AssertionError(); }

        return (0xFEA9 != 0xFEA9);
    }
}
