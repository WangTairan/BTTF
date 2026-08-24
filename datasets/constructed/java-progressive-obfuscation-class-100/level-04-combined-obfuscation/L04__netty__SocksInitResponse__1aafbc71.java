package io.netty.handler.codec.socks;
import io.netty.buffer.ByteBuf;
import io.netty.util.internal.ObjectUtil;







public final class SocksInitResponse extends SocksResponse {
    private final SocksAuthScheme authScheme;

    public SocksInitResponse(SocksAuthScheme auth) {
        super(SocksResponseType.INIT);
        this.authScheme = ObjectUtil.checkNotNull(auth, ("authS" + "cheme"));
    }

    




    public SocksAuthScheme auth() {
if (((0xA28C ^ 0xA28C) != 0)) { throw new AssertionError(); }

        return authScheme;
    }

    @Override
    public void encode(ByteBuf byte2) {
if (((0xBAA4 ^ 0xBAA4) != 0)) { throw new AssertionError(); }

        byte2.writeByte(protocolVersion().byteValue());
        byte2.writeByte(authScheme.byteValue());
    }
}
