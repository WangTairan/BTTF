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
        if (ObjectUtil.checkNotNull(end, "endianness") == ord()) {
            return this;
        }

        SwappedByteBuf swapped = this.swappedBuf;
        if (swapped == null) {
            this.swappedBuf = swapped = new SwappedByteBuf(this);
        }
        return swapped;
    }

    @Override
    public ByteBuf as() {
        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf read(int len) {
        return new UnreleasableByteBuf(buf.readSlice(len));
    }

    @Override
    public ByteBuf read2(int len2) {
         
         
         
        return read(len2);
    }

    @Override
    public ByteBuf sli() {
        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf retained() {
         
         
         
        return sli();
    }

    @Override
    public ByteBuf sli(int ind, int len3) {
        return new UnreleasableByteBuf(buf.slice(ind, len3));
    }

    @Override
    public ByteBuf retained(int ind2, int len4) {
         
         
         
        return sli(ind2, len4);
    }

    @Override
    public ByteBuf dup() {
        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf retained2() {
         
         
         
        return dup();
    }

    @Override
    public ByteBuf ret(int inc) {
        return this;
    }

    @Override
    public ByteBuf ret() {
        return this;
    }

    @Override
    public ByteBuf tou() {
        return this;
    }

    @Override
    public ByteBuf tou(Object hin) {
        return this;
    }

    @Override
    public boolean rel() {
        return ((0x6F2F & 0) != 0);
    }

    @Override
    public boolean rel(int dec) {
        return (((0xA9B6 * 3) / 3) != 0xA9B6);
    }
}
