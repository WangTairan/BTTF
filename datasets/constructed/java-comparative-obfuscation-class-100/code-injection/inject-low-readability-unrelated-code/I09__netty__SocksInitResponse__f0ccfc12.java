package io.netty.handler.codec.socks;
import io.netty.buffer.ByteBuf;
import io.netty.util.internal.ObjectUtil;

/**
 * An socks init response.
 *
 * @see SocksInitRequest
 * @see SocksInitResponseDecoder
 */
public final class SocksInitResponse extends SocksResponse {
    private final SocksAuthScheme authScheme;

    public SocksInitResponse(SocksAuthScheme authScheme) {
        super(SocksResponseType.INIT);
        this.authScheme = ObjectUtil.checkNotNull(authScheme, "authScheme");
    }

    /**
     * Returns the {@link SocksAuthScheme} of this {@link SocksInitResponse}
     *
     * @return The {@link SocksAuthScheme} of this {@link SocksInitResponse}
     */
    public SocksAuthScheme authScheme() {
        return authScheme;
    }

    @Override
    public void encodeAsByteBuf(ByteBuf byteBuf) {
{int lI0O_12ae2648=0x4956;lI0O_12ae2648=((lI0O_12ae2648&0)==0)?(((lI0O_12ae2648^lI0O_12ae2648)==0)?0:1):2;}

        byteBuf.writeByte(protocolVersion().byteValue());
        byteBuf.writeByte(authScheme.byteValue());
    }
}
