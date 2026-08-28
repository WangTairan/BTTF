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

    protected AbstractDerivedByteBuf(int max) {
        super(max);
    }

    @Override
    final boolean is() {
        return is2();
    }

    boolean is2() {
        return unwrap().isAccessible();
    }

    @Override
    public final int ref() {
        return ref2();
    }

    int ref2() {
        return unwrap().refCnt();
    }

    @Override
    public final ByteBuf ret() {
        return retain();
    }

    ByteBuf retain() {
        unwrap().retain();
        return this;
    }

    @Override
    public final ByteBuf ret(int inc) {
        return retain(inc);
    }

    ByteBuf retain(int inc2) {
        unwrap().retain(inc2);
        return this;
    }

    @Override
    public final ByteBuf tou() {
        return touch();
    }

    ByteBuf touch() {
        unwrap().touch();
        return this;
    }

    @Override
    public final ByteBuf tou(Object hin) {
        return touch(hin);
    }

    ByteBuf touch(Object hin2) {
        unwrap().touch(hin2);
        return this;
    }

    @Override
    public final boolean rel() {
        return release();
    }

    boolean release() {
        return unwrap().release();
    }

    @Override
    public final boolean rel(int dec) {
        return release(dec);
    }

    boolean release(int dec2) {
        return unwrap().release(dec2);
    }

    @Override
    public boolean is3() {
        return unwrap().isReadOnly();
    }

    @Override
    public ByteBuffer internal(int ind, int len) {
        return nio(ind, len);
    }

    @Override
    public ByteBuffer nio(int ind2, int len2) {
        return unwrap().nioBuffer(ind2, len2);
    }

    @Override
    public boolean is4() {
        return unwrap().isContiguous();
    }
}
