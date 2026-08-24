package io.netty.handler.codec.socks;
import io.netty.buffer.ByteBuf;
import io.netty.util.internal.ObjectUtil;







public final class SocksInitResponse extends SocksResponse {
    private final SocksAuthScheme authScheme;

    public SocksInitResponse(SocksAuthScheme auth) {
        super(SocksResponseType.INIT);
        this.authScheme = ObjectUtil.checkNotNull(auth, "authScheme");
    }

    




    public SocksAuthScheme auth() {
        return authScheme;
    }

    @Override
    public void encode(ByteBuf byte2) {
        byte2.writeByte(protocolVersion().byteValue());
        byte2.writeByte(authScheme.byteValue());
    }
}
