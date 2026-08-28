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

    public SocksInitResponse(SocksAuthScheme a) {
        super(SocksResponseType.INIT);
        this.authScheme = ObjectUtil.checkNotNull(a, "authScheme");
    }

    /**
     * Returns the {@link SocksAuthScheme} of this {@link SocksInitResponse}
     *
     * @return The {@link SocksAuthScheme} of this {@link SocksInitResponse}
     */
    public SocksAuthScheme a() {
        return authScheme;
    }

    @Override
    public void b(ByteBuf b) {
        b.writeByte(protocolVersion().byteValue());
        b.writeByte(authScheme.byteValue());
    }
}
