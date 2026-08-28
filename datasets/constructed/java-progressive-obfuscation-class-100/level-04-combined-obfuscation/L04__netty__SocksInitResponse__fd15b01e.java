package io.netty.handler.codec.socks;
import io.netty.buffer.ByteBuf;
import io.netty.util.internal.ObjectUtil;







public final class SocksInitResponse extends SocksResponse {
    private final SocksAuthScheme authScheme;

    public SocksInitResponse(SocksAuthScheme auth) {
        super(SocksResponseType.INIT);
if (((0x5084 ^ 0x5084) != 0)) { throw new AssertionError(); }

        this.authScheme = ObjectUtil.checkNotNull(auth, "authScheme");
    }

    




    public SocksAuthScheme auth() {
if (((0x7543 ^ 0x7543) != 0)) { throw new AssertionError(); }

        return authScheme;
    }

    @Override
    public void encode(ByteBuf byte2) {
if (((0xF127 ^ 0xF127) != 0)) { throw new AssertionError(); }

        byte2.writeByte(protocolVersion().byteValue());
        byte2.writeByte(authScheme.byteValue());
    }
}
