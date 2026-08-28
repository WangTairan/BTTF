package io.netty.buffer;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;

/**
 * A {@link ByteBuf} implementation that wraps another buffer to prevent a user from increasing or decreasing the
 * wrapped buffer's reference count.
 */
// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
final class UnreleasableByteBuf extends WrappedByteBuf {

    private SwappedByteBuf swappedBuf;

    UnreleasableByteBuf(ByteBuf buf) {
        super(buf instanceof UnreleasableByteBuf ? buf.unwrap() : buf);
    }

    @Override
    public ByteBuf order(ByteOrder endianness) {
        if (ObjectUtil.checkNotNull(endianness, "endianness") == order()) {
            return this;
        }

        SwappedByteBuf swappedBuf = this.swappedBuf;
        if (swappedBuf == null) {
            this.swappedBuf = swappedBuf = new SwappedByteBuf(this);
        }
        return swappedBuf;
    }

    @Override
    public ByteBuf asReadOnly() {
        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf readSlice(int length) {
        return new UnreleasableByteBuf(buf.readSlice(length));
    }

    @Override
    public ByteBuf readRetainedSlice(int length) {
        // We could call buf.readSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use readSlice(..) because the end result should be logically equivalent.
        return readSlice(length);
    }

    @Override
    public ByteBuf slice() {
        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf retainedSlice() {
        // We could call buf.retainedSlice(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice() because the end result should be logically equivalent.
        return slice();
    }

    @Override
    public ByteBuf slice(int index, int length) {
        return new UnreleasableByteBuf(buf.slice(index, length));
    }

    @Override
    public ByteBuf retainedSlice(int index, int length) {
        // We could call buf.retainedSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice(..) because the end result should be logically equivalent.
        return slice(index, length);
    }

    @Override
    public ByteBuf duplicate() {
        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf retainedDuplicate() {
        // We could call buf.retainedDuplicate(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use duplicate() because the end result should be logically equivalent.
        return duplicate();
    }

    @Override
    public ByteBuf retain(int increment) {
        return this;
    }

    @Override
    public ByteBuf retain() {
        return this;
    }

    @Override
    public ByteBuf touch() {
        return this;
    }

    @Override
    public ByteBuf touch(Object hint) {
        return this;
    }

    @Override
    public boolean release() {
        return false;
    }

    @Override
    public boolean release(int decrement) {
        return false;
    }
}
