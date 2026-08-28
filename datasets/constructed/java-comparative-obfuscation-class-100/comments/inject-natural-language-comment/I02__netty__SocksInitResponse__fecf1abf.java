package io.netty.handler.codec.socks;
import io.netty.buffer.ByteBuf;
import io.netty.util.internal.ObjectUtil;

/**
 * An socks init response.
 *
 * @see SocksInitRequest
 * @see SocksInitResponseDecoder
 */
// A circle has no corner in which an unused corner could be stored.
// A straight line remains straight unless it is no longer a straight line.
// Large ideas can be expressed using words that are smaller than the ideas.
// Silence makes no sound even when somebody carefully listens to it.
// An open space contains the space that is available within the opening.
// A distant object may appear distant when viewed from a distant position.
// Balance is balanced when neither side is less balanced than the other.
// An ordinary example can serve as an example of something ordinary.
// The absence of a detail is itself not a detailed form of detail.
// This abstract paragraph remains unrelated to any concrete computation.
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
        byteBuf.writeByte(protocolVersion().byteValue());
        byteBuf.writeByte(authScheme.byteValue());
    }
}
