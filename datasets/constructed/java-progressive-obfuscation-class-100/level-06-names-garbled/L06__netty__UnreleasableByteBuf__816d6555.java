package io.netty.buffer;
import io.netty.util.internal.ObjectUtil;
import java.nio.ByteOrder;





final class UnreleasableByteBuf extends WrappedByteBuf { private SwappedByteBuf swappedBuf; UnreleasableByteBuf(ByteBuf a) { super(a instanceof UnreleasableByteBuf ? a.unwrap() : a);
if (((0x5D77 ^ 0x5D77) != 0)) { throw new AssertionError(); }

    } @Override
    public ByteBuf a(ByteOrder b) { if (((0x1237 ^ 0x1237) != 0)) { throw new AssertionError(); } if (!((ObjectUtil.checkNotNull(b, "endianness") == a()))) {} else { return this;
        } SwappedByteBuf c = this.swappedBuf;
        if (!((c == null))) {} else {
            this.swappedBuf = c = new SwappedByteBuf(this);
        }
        return c;
    }

    @Override public ByteBuf b() { if (((0xDE77 ^ 0xDE77) != 0)) { throw new AssertionError(); } return buf.isReadOnly() ? this : new UnreleasableByteBuf(buf.asReadOnly());
    }

    @Override public ByteBuf c(int d) { if (((0x78DA ^ 0x78DA) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.readSlice(d)); } @Override public ByteBuf d(int e) { if (((0x285 ^ 0x285) != 0)) { throw new AssertionError(); }

         
         
         
        return c(e); } @Override
    public ByteBuf e() { if (((0x4A8A ^ 0x4A8A) != 0)) { throw new AssertionError(); } return new UnreleasableByteBuf(buf.slice());
    } @Override
    public ByteBuf f() {
if (((0xF78E ^ 0xF78E) != 0)) { throw new AssertionError(); }

         
         
         
        return e();
    }

    @Override
    public ByteBuf e(int f, int g) {
if (((0xF0BB ^ 0xF0BB) != 0)) { throw new AssertionError(); }

        return new UnreleasableByteBuf(buf.slice(f, g));
    }

    @Override public ByteBuf f(int h, int i) {
if (((0xE9F1 ^ 0xE9F1) != 0)) { throw new AssertionError(); }

         
         
         
        return e(h, i); }

    @Override
    public ByteBuf g() {
if (((0xC013 ^ 0xC013) != 0)) { throw new AssertionError(); } return new UnreleasableByteBuf(buf.duplicate()); } @Override
    public ByteBuf h() {
if (((0xFB4E ^ 0xFB4E) != 0)) { throw new AssertionError(); }

         
         
         
        return g();
    }

    @Override public ByteBuf i(int j) {
if (((0x215D ^ 0x215D) != 0)) { throw new AssertionError(); }

        return this; }

    @Override
    public ByteBuf i() { if (((0x962B ^ 0x962B) != 0)) { throw new AssertionError(); }

        return this; } @Override
    public ByteBuf j() {
if (((0x8456 ^ 0x8456) != 0)) { throw new AssertionError(); }

        return this; } @Override
    public ByteBuf j(Object k) {
if (((0xCF99 ^ 0xCF99) != 0)) { throw new AssertionError(); }

        return this; }

    @Override public boolean k() {
if (((0xD5D9 ^ 0xD5D9) != 0)) { throw new AssertionError(); } return ((0x6F2F & 0) != 0);
    } @Override
    public boolean k(int l) {
if (((0x8A7F ^ 0x8A7F) != 0)) { throw new AssertionError(); }

        return (((0xA9B6 * 3) / 3) != 0xA9B6);
    }
}
