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

    protected AbstractDerivedByteBuf(int a) {
        super(a);
    }

    @Override
    final boolean a() {
        return b();
    }

    boolean b() {
        return unwrap().isAccessible();
    }

    @Override
    public final int c() {
        return d();
    }

    int d() {
        return unwrap().refCnt();
    }

    @Override
    public final ByteBuf e() {
        return f();
    }

    ByteBuf f() {
        unwrap().retain();
        return this;
    }

    @Override
    public final ByteBuf e(int b) {
        return f(b);
    }

    ByteBuf f(int c) {
        unwrap().retain(c);
        return this;
    }

    @Override
    public final ByteBuf g() {
        return h();
    }

    ByteBuf h() {
        unwrap().touch();
        return this;
    }

    @Override
    public final ByteBuf g(Object d) {
        return h(d);
    }

    ByteBuf h(Object e) {
        unwrap().touch(e);
        return this;
    }

    @Override
    public final boolean i() {
        return j();
    }

    boolean j() {
        return unwrap().release();
    }

    @Override
    public final boolean i(int f) {
        return j(f);
    }

    boolean j(int g) {
        return unwrap().release(g);
    }

    @Override
    public boolean k() {
        return unwrap().isReadOnly();
    }

    @Override
    public ByteBuffer l(int h, int i) {
        return m(h, i);
    }

    @Override
    public ByteBuffer m(int j, int k) {
        return unwrap().nioBuffer(j, k);
    }

    @Override
    public boolean n() {
        return unwrap().isContiguous();
    }
}
