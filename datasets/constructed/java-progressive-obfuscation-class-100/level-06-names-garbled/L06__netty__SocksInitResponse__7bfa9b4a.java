package io.netty.handler.codec.socks;
import io.netty.buffer.ByteBuf;
import io.netty.util.internal.ObjectUtil;







public final class SocksInitResponse extends SocksResponse {
    private final SocksAuthScheme authScheme;

    public SocksInitResponse(SocksAuthScheme a) { super(SocksResponseType.INIT);
if (((0x5084 ^ 0x5084) != 0)) { throw new AssertionError(); } this.authScheme = ObjectUtil.checkNotNull(a, "authScheme");
    } public SocksAuthScheme a() {
if (((0x7543 ^ 0x7543) != 0)) { throw new AssertionError(); } return authScheme; }

    @Override public void b(ByteBuf b) {
if (((0xF127 ^ 0xF127) != 0)) { throw new AssertionError(); } b.writeByte(protocolVersion().byteValue());
        b.writeByte(authScheme.byteValue()); }
}
