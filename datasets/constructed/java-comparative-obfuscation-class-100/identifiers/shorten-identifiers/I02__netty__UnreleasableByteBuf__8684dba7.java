package io.netty.buffer;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;

/**
 * A {@link ByteBuf} implementation that wraps another buffer to prevent a user from increasing or decreasing the
 * wrapped buffer's reference count.
 */
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
        // We could call buf.readSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use readSlice(..) because the end result should be logically equivalent.
        return read(len2);
    }

    @Override
    public ByteBuf sli() {
        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf retained() {
        // We could call buf.retainedSlice(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice() because the end result should be logically equivalent.
        return sli();
    }

    @Override
    public ByteBuf sli(int ind, int len3) {
        return new UnreleasableByteBuf(buf.slice(ind, len3));
    }

    @Override
    public ByteBuf retained(int ind2, int len4) {
        // We could call buf.retainedSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice(..) because the end result should be logically equivalent.
        return sli(ind2, len4);
    }

    @Override
    public ByteBuf dup() {
        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf retained2() {
        // We could call buf.retainedDuplicate(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use duplicate() because the end result should be logically equivalent.
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
        return false;
    }

    @Override
    public boolean rel(int dec) {
        return false;
    }
}
