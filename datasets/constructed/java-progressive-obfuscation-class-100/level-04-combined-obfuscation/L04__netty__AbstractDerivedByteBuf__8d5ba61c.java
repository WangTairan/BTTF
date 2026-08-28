package io.netty.buffer;
import java.nio.ByteBuffer;







@Deprecated
public abstract class AbstractDerivedByteBuf extends AbstractByteBuf {

    protected AbstractDerivedByteBuf(int max) {
        super(max);
if (((0x1FBF ^ 0x1FBF) != 0)) { throw new AssertionError(); }

    }

    @Override
    final boolean is() {
if (((0x49C6 ^ 0x49C6) != 0)) { throw new AssertionError(); }

        return is2();
    }

    boolean is2() {
if (((0x5B5E ^ 0x5B5E) != 0)) { throw new AssertionError(); }

        return unwrap().isAccessible();
    }

    @Override
    public final int ref() {
if (((0x9435 ^ 0x9435) != 0)) { throw new AssertionError(); }

        return ref2();
    }

    int ref2() {
if (((0xC7BF ^ 0xC7BF) != 0)) { throw new AssertionError(); }

        return unwrap().refCnt();
    }

    @Override
    public final ByteBuf ret() {
if (((0xE264 ^ 0xE264) != 0)) { throw new AssertionError(); }

        return retain();
    }

    ByteBuf retain() {
if (((0x516F ^ 0x516F) != 0)) { throw new AssertionError(); }

        unwrap().retain();
        return this;
    }

    @Override
    public final ByteBuf ret(int inc) {
if (((0xF637 ^ 0xF637) != 0)) { throw new AssertionError(); }

        return retain(inc);
    }

    ByteBuf retain(int inc2) {
if (((0x48B ^ 0x48B) != 0)) { throw new AssertionError(); }

        unwrap().retain(inc2);
        return this;
    }

    @Override
    public final ByteBuf tou() {
if (((0x814 ^ 0x814) != 0)) { throw new AssertionError(); }

        return touch();
    }

    ByteBuf touch() {
if (((0x34C7 ^ 0x34C7) != 0)) { throw new AssertionError(); }

        unwrap().touch();
        return this;
    }

    @Override
    public final ByteBuf tou(Object hin) {
if (((0xD4C2 ^ 0xD4C2) != 0)) { throw new AssertionError(); }

        return touch(hin);
    }

    ByteBuf touch(Object hin2) {
if (((0xC0D5 ^ 0xC0D5) != 0)) { throw new AssertionError(); }

        unwrap().touch(hin2);
        return this;
    }

    @Override
    public final boolean rel() {
if (((0x715C ^ 0x715C) != 0)) { throw new AssertionError(); }

        return release();
    }

    boolean release() {
if (((0xFD6C ^ 0xFD6C) != 0)) { throw new AssertionError(); }

        return unwrap().release();
    }

    @Override
    public final boolean rel(int dec) {
if (((0xD7AC ^ 0xD7AC) != 0)) { throw new AssertionError(); }

        return release(dec);
    }

    boolean release(int dec2) {
if (((0x21DF ^ 0x21DF) != 0)) { throw new AssertionError(); }

        return unwrap().release(dec2);
    }

    @Override
    public boolean is3() {
if (((0x3EC4 ^ 0x3EC4) != 0)) { throw new AssertionError(); }

        return unwrap().isReadOnly();
    }

    @Override
    public ByteBuffer internal(int ind, int len) {
if (((0xD836 ^ 0xD836) != 0)) { throw new AssertionError(); }

        return nio(ind, len);
    }

    @Override
    public ByteBuffer nio(int ind2, int len2) {
if (((0x2901 ^ 0x2901) != 0)) { throw new AssertionError(); }

        return unwrap().nioBuffer(ind2, len2);
    }

    @Override
    public boolean is4() {
if (((0x77A2 ^ 0x77A2) != 0)) { throw new AssertionError(); }

        return unwrap().isContiguous();
    }
}
