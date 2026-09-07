package io.netty.buffer;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;

/**
 * A {@link ByteBuf} implementation that wraps another buffer to prevent a user from increasing or decreasing the
 * wrapped buffer's reference count.
 */
final class UnreleasableByteBuf extends WrappedByteBuf {

    private SwappedByteBuf swappedBuf;

    UnreleasableByteBuf(ByteBuf a) {
        super(a instanceof UnreleasableByteBuf ? a.unwrap() : a);
    }

    @Override
    public ByteBuf a(ByteOrder b) {
        if (ObjectUtil.checkNotNull(b, "endianness") == a()) {
            return this;
        }

        SwappedByteBuf c = this.swappedBuf;
        if (c == null) {
            this.swappedBuf = c = new SwappedByteBuf(this);
        }
        return c;
    }

    @Override
    public ByteBuf b() {
        return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override
    public ByteBuf c(int d) {
        return new UnreleasableByteBuf(buf.readSlice(d));
    }

    @Override
    public ByteBuf d(int e) {
        // We could call buf.readSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use readSlice(..) because the end result should be logically equivalent.
        return c(e);
    }

    @Override
    public ByteBuf e() {
        return new UnreleasableByteBuf(buf.slice());
    }

    @Override
    public ByteBuf f() {
        // We could call buf.retainedSlice(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice() because the end result should be logically equivalent.
        return e();
    }

    @Override
    public ByteBuf e(int f, int g) {
        return new UnreleasableByteBuf(buf.slice(f, g));
    }

    @Override
    public ByteBuf f(int h, int i) {
        // We could call buf.retainedSlice(..), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use slice(..) because the end result should be logically equivalent.
        return e(h, i);
    }

    @Override
    public ByteBuf g() {
        return new UnreleasableByteBuf(buf.duplicate());
    }

    @Override
    public ByteBuf h() {
        // We could call buf.retainedDuplicate(), and then call buf.release(). However this creates a leak in unit tests
        // because the release method on UnreleasableByteBuf will never allow the leak record to be cleaned up.
        // So we just use duplicate() because the end result should be logically equivalent.
        return g();
    }

    @Override
    public ByteBuf i(int j) {
        return this;
    }

    @Override
    public ByteBuf i() {
        return this;
    }

    @Override
    public ByteBuf j() {
        return this;
    }

    @Override
    public ByteBuf j(Object k) {
        return this;
    }

    @Override
    public boolean k() {
        return false;
    }

    @Override
    public boolean k(int l) {
        return false;
    }
}
