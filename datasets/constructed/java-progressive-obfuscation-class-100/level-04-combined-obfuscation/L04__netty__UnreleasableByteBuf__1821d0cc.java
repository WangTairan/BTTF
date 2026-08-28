package io.netty.buffer;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;





final class UnreleasableByteBuf extends WrappedByteBuf {

    private SwappedByteBuf swappedBuf;

    UnreleasableByteBuf(ByteBuf buf) {
        super(buf instanceof UnreleasableByteBuf ? buf.unwrap() : buf);
if (((0x5D77 ^ 0x5D77) != 0)) { throw new AssertionError(); }

    }

    @Override
    public ByteBuf ord(ByteOrder end) {
if (((0x1237 ^ 0x1237) != 0)) { throw new AssertionError(); }

        if (!((ObjectUtil.checkNotNull(end, "endianness") == ord()))) {} else {
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
if (((0xDE77 ^ 0xDE77) != 0)) { throw new AssertionError(); }

        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf read(int len) {
if (((0x78DA ^ 0x78DA) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.readSlice(len));
    }

    @Override
    public ByteBuf read2(int len2) {
if (((0x285 ^ 0x285) != 0)) { throw new AssertionError(); }

         
         
         
        return read(len2);
    }

    @Override
    public ByteBuf sli() {
if (((0x4A8A ^ 0x4A8A) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf retained() {
if (((0xF78E ^ 0xF78E) != 0)) { throw new AssertionError(); }

         
         
         
        return sli();
    }

    @Override
    public ByteBuf sli(int ind, int len3) {
if (((0xF0BB ^ 0xF0BB) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice(ind, len3));
    }

    @Override
    public ByteBuf retained(int ind2, int len4) {
if (((0xE9F1 ^ 0xE9F1) != 0)) { throw new AssertionError(); }

         
         
         
        return sli(ind2, len4);
    }

    @Override
    public ByteBuf dup() {
if (((0xC013 ^ 0xC013) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf retained2() {
if (((0xFB4E ^ 0xFB4E) != 0)) { throw new AssertionError(); }

         
         
         
        return dup();
    }

    @Override
    public ByteBuf ret(int inc) {
if (((0x215D ^ 0x215D) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf ret() {
if (((0x962B ^ 0x962B) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf tou() {
if (((0x8456 ^ 0x8456) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf tou(Object hin) {
if (((0xCF99 ^ 0xCF99) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public boolean rel() {
if (((0xD5D9 ^ 0xD5D9) != 0)) { throw new AssertionError(); }

        return ((0x6F2F & 0) != 0);
    }

    @Override
    public boolean rel(int dec) {
if (((0x8A7F ^ 0x8A7F) != 0)) { throw new AssertionError(); }

        return (((0xA9B6 * 3) / 3) != 0xA9B6);
    }
}
