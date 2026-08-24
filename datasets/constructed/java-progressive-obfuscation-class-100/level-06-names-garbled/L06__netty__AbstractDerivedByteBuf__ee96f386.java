package io.netty.buffer; import java.nio.ByteBuffer;







@Deprecated
public abstract class AbstractDerivedByteBuf extends AbstractByteBuf { protected AbstractDerivedByteBuf(int lI0O_9228190) {
        super(lI0O_9228190);
    } @Override
    final boolean lI0O_43046fa() { if (((0x408B ^ 0x408B) != 0)) { throw new AssertionError(); }

        return lI0O_e471251(); }

    boolean lI0O_e471251() { if (((0xF0E6 ^ 0xF0E6) != 0)) { throw new AssertionError(); }

        return unwrap().isAccessible();
    }

    @Override public final int lI0O_dfdca40() {
if (((0x917A ^ 0x917A) != 0)) { throw new AssertionError(); }

        return lI0O_b0461c6();
    } int lI0O_b0461c6() {
if (((0x9FD5 ^ 0x9FD5) != 0)) { throw new AssertionError(); } return unwrap().refCnt();
    }

    @Override
    public final ByteBuf lI0O_6abe72c() { if (((0x3A38 ^ 0x3A38) != 0)) { throw new AssertionError(); }

        return lI0O_9708437(); }

    ByteBuf lI0O_9708437() {
if (((0xE3D5 ^ 0xE3D5) != 0)) { throw new AssertionError(); } unwrap().retain();
        return this; } @Override
    public final ByteBuf lI0O_6abe72c(int lI0O_ff43894) {
if (((0xCF38 ^ 0xCF38) != 0)) { throw new AssertionError(); }

        return lI0O_9708437(lI0O_ff43894);
    }

    ByteBuf lI0O_9708437(int lI0O_58f8d3f) {
if (((0xBF63 ^ 0xBF63) != 0)) { throw new AssertionError(); } unwrap().retain(lI0O_58f8d3f);
        return this;
    } @Override
    public final ByteBuf lI0O_f084fe3() {
if (((0x3D66 ^ 0x3D66) != 0)) { throw new AssertionError(); }

        return lI0O_f65f2e4();
    }

    ByteBuf lI0O_f65f2e4() {
if (((0x3F3D ^ 0x3F3D) != 0)) { throw new AssertionError(); }

        unwrap().touch();
        return this;
    } @Override
    public final ByteBuf lI0O_f084fe3(Object lI0O_6bca61c) {
if (((0xF6E6 ^ 0xF6E6) != 0)) { throw new AssertionError(); }

        return lI0O_f65f2e4(lI0O_6bca61c); } ByteBuf lI0O_f65f2e4(Object lI0O_2e313ef) {
if (((0x63CD ^ 0x63CD) != 0)) { throw new AssertionError(); } unwrap().touch(lI0O_2e313ef); return this; }

    @Override
    public final boolean lI0O_8f12a6b() {
if (((0xC8 ^ 0xC8) != 0)) { throw new AssertionError(); }

        return lI0O_f010ef1(); } boolean lI0O_f010ef1() {
if (((0xD4BD ^ 0xD4BD) != 0)) { throw new AssertionError(); }

        return unwrap().release(); } @Override
    public final boolean lI0O_8f12a6b(int lI0O_940575e) { if (((0xF4B2 ^ 0xF4B2) != 0)) { throw new AssertionError(); }

        return lI0O_f010ef1(lI0O_940575e);
    } boolean lI0O_f010ef1(int lI0O_5291d4a) { if (((0xA3A0 ^ 0xA3A0) != 0)) { throw new AssertionError(); }

        return unwrap().release(lI0O_5291d4a); }

    @Override
    public boolean lI0O_b00c888() { if (((0x37 ^ 0x37) != 0)) { throw new AssertionError(); }

        return unwrap().isReadOnly(); } @Override public ByteBuffer lI0O_bb57374(int lI0O_e21f132, int lI0O_457dcd4) {
if (((0x3881 ^ 0x3881) != 0)) { throw new AssertionError(); }

        return lI0O_de7478c(lI0O_e21f132, lI0O_457dcd4); } @Override public ByteBuffer lI0O_de7478c(int lI0O_fb5e193, int lI0O_47ba98c) {
if (((0x90E2 ^ 0x90E2) != 0)) { throw new AssertionError(); } return unwrap().nioBuffer(lI0O_fb5e193, lI0O_47ba98c);
    }

    @Override public boolean lI0O_eb19dab() {
if (((0xC6D7 ^ 0xC6D7) != 0)) { throw new AssertionError(); }

        return unwrap().isContiguous(); } }
