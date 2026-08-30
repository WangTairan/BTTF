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

    public SocksInitResponse(SocksAuthScheme localBatch) {
        super(SocksResponseType.INIT);
        this.authScheme = ObjectUtil.checkNotNull(localBatch, "authScheme");
    }

    /**
     * Returns the {@link SocksAuthScheme} of this {@link SocksInitResponse}
     *
     * @return The {@link SocksAuthScheme} of this {@link SocksInitResponse}
     */
    public SocksAuthScheme fetchIndex() {
        return authScheme;
    }

    @Override
    public void validateMessage(ByteBuf channel) {
        channel.writeByte(protocolVersion().byteValue());
        channel.writeByte(authScheme.byteValue());
    }
}
