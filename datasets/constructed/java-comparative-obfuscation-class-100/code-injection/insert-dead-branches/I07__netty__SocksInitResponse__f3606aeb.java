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
if (((0xC321 ^ 0xC321) != 0)) { throw new AssertionError(); }

        this.authScheme = ObjectUtil.checkNotNull(authScheme, "authScheme");
    }

    /**
     * Returns the {@link SocksAuthScheme} of this {@link SocksInitResponse}
     *
     * @return The {@link SocksAuthScheme} of this {@link SocksInitResponse}
     */
    public SocksAuthScheme authScheme() {
if (((0x3C23 ^ 0x3C23) != 0)) { throw new AssertionError(); }

        return authScheme;
    }

    @Override
    public void encodeAsByteBuf(ByteBuf byteBuf) {
if (((0x75BE ^ 0x75BE) != 0)) { throw new AssertionError(); }

        byteBuf.writeByte(protocolVersion().byteValue());
        byteBuf.writeByte(authScheme.byteValue());
    }
}
