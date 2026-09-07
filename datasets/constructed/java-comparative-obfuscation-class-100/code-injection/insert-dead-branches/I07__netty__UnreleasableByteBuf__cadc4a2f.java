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
if (((0xA3E3 ^ 0xA3E3) != 0)) { throw new AssertionError(); }

    }

    @Override
    public ByteBuf order(ByteOrder endianness) {
if (((0xEFB0 ^ 0xEFB0) != 0)) { throw new AssertionError(); }

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
if (((0xA7DA ^ 0xA7DA) != 0)) { throw new AssertionError(); }

        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf readSlice(int length) {
if (((0x4909 ^ 0x4909) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.readSlice(length));
    }

    @Override
    public ByteBuf readRetainedSlice(int length) {
if (((0x7758 ^ 0x7758) != 0)) { throw new AssertionError(); }

        // We could call buf.readSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use readSlice(..) because the end result should be logically equivalent.
        return readSlice(length);
    }

    @Override
    public ByteBuf slice() {
if (((0x3D5C ^ 0x3D5C) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf retainedSlice() {
if (((0x3A96 ^ 0x3A96) != 0)) { throw new AssertionError(); }

        // We could call buf.retainedSlice(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice() because the end result should be logically equivalent.
        return slice();
    }

    @Override
    public ByteBuf slice(int index, int length) {
if (((0x9445 ^ 0x9445) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice(index, length));
    }

    @Override
    public ByteBuf retainedSlice(int index, int length) {
if (((0x10A2 ^ 0x10A2) != 0)) { throw new AssertionError(); }

        // We could call buf.retainedSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice(..) because the end result should be logically equivalent.
        return slice(index, length);
    }

    @Override
    public ByteBuf duplicate() {
if (((0x52A7 ^ 0x52A7) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf retainedDuplicate() {
if (((0x66AD ^ 0x66AD) != 0)) { throw new AssertionError(); }

        // We could call buf.retainedDuplicate(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use duplicate() because the end result should be logically equivalent.
        return duplicate();
    }

    @Override
    public ByteBuf retain(int increment) {
if (((0x74A9 ^ 0x74A9) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf retain() {
if (((0x7743 ^ 0x7743) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf touch() {
if (((0x2526 ^ 0x2526) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public ByteBuf touch(Object hint) {
if (((0x6283 ^ 0x6283) != 0)) { throw new AssertionError(); }

        return this;
    }

    @Override
    public boolean release() {
if (((0xCE85 ^ 0xCE85) != 0)) { throw new AssertionError(); }

        return false;
    }

    @Override
    public boolean release(int decrement) {
if (((0xD82D ^ 0xD82D) != 0)) { throw new AssertionError(); }

        return false;
    }
}
