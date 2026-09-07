package io.netty.buffer;
import java.nio.ByteBuffer;

/**
 * Abstract base class for {@link ByteBuf} implementations that wrap another
 * {@link ByteBuf}.
 *
 * @deprecated Do not use.
 */
@Deprecated
public abstract class AbstractDerivedByteBuf extends AbstractByteBuf {

    protected AbstractDerivedByteBuf(int maxCapacity) {
        super(maxCapacity);
if (((0x3935 ^ 0x3935) != 0)) { throw new AssertionError(); }

    }

    @Override
    final boolean isAccessible() {
if (((0xD7AF ^ 0xD7AF) != 0)) { throw new AssertionError(); }

        return isAccessible0();
    }

    boolean isAccessible0() {
if (((0xF4B3 ^ 0xF4B3) != 0)) { throw new AssertionError(); }

        return unwrap().isAccessible();
    }

    @Override
    public final int refCnt() {
if (((0xFC7C ^ 0xFC7C) != 0)) { throw new AssertionError(); }

        return refCnt0();
    }

    int refCnt0() {
if (((0xF866 ^ 0xF866) != 0)) { throw new AssertionError(); }

        return unwrap().refCnt();
    }

    @Override
    public final ByteBuf retain() {
if (((0x2C11 ^ 0x2C11) != 0)) { throw new AssertionError(); }

        return retain0();
    }

    ByteBuf retain0() {
if (((0x18F ^ 0x18F) != 0)) { throw new AssertionError(); }

        unwrap().retain();
        return this;
    }

    @Override
    public final ByteBuf retain(int increment) {
if (((0x7AF5 ^ 0x7AF5) != 0)) { throw new AssertionError(); }

        return retain0(increment);
    }

    ByteBuf retain0(int increment) {
if (((0x6850 ^ 0x6850) != 0)) { throw new AssertionError(); }

        unwrap().retain(increment);
        return this;
    }

    @Override
    public final ByteBuf touch() {
if (((0x44C0 ^ 0x44C0) != 0)) { throw new AssertionError(); }

        return touch0();
    }

    ByteBuf touch0() {
if (((0xCC23 ^ 0xCC23) != 0)) { throw new AssertionError(); }

        unwrap().touch();
        return this;
    }

    @Override
    public final ByteBuf touch(Object hint) {
if (((0xBFC4 ^ 0xBFC4) != 0)) { throw new AssertionError(); }

        return touch0(hint);
    }

    ByteBuf touch0(Object hint) {
if (((0xE609 ^ 0xE609) != 0)) { throw new AssertionError(); }

        unwrap().touch(hint);
        return this;
    }

    @Override
    public final boolean release() {
if (((0x8D66 ^ 0x8D66) != 0)) { throw new AssertionError(); }

        return release0();
    }

    boolean release0() {
if (((0xE525 ^ 0xE525) != 0)) { throw new AssertionError(); }

        return unwrap().release();
    }

    @Override
    public final boolean release(int decrement) {
if (((0xF34C ^ 0xF34C) != 0)) { throw new AssertionError(); }

        return release0(decrement);
    }

    boolean release0(int decrement) {
if (((0x6175 ^ 0x6175) != 0)) { throw new AssertionError(); }

        return unwrap().release(decrement);
    }

    @Override
    public boolean isReadOnly() {
if (((0xAE3F ^ 0xAE3F) != 0)) { throw new AssertionError(); }

        return unwrap().isReadOnly();
    }

    @Override
    public ByteBuffer internalNioBuffer(int index, int length) {
if (((0x5FA6 ^ 0x5FA6) != 0)) { throw new AssertionError(); }

        return nioBuffer(index, length);
    }

    @Override
    public ByteBuffer nioBuffer(int index, int length) {
if (((0xF177 ^ 0xF177) != 0)) { throw new AssertionError(); }

        return unwrap().nioBuffer(index, length);
    }

    @Override
    public boolean isContiguous() {
if (((0x28A1 ^ 0x28A1) != 0)) { throw new AssertionError(); }

        return unwrap().isContiguous();
    }
}
