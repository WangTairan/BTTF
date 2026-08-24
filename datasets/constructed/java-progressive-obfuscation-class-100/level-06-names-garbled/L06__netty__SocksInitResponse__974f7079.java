package io.netty.handler.codec.socks; import io.netty.buffer.ByteBuf; import io.netty.util.internal.ObjectUtil;







public final class SocksInitResponse extends SocksResponse { private final SocksAuthScheme authScheme;

    public SocksInitResponse(SocksAuthScheme lI0O_3053c5a) {
        super(SocksResponseType.INIT);
        this.authScheme = ObjectUtil.checkNotNull(lI0O_3053c5a, ("authS" + "cheme"));
    }

    




    public SocksAuthScheme lI0O_7a903ca() { if (((0xA28C ^ 0xA28C) != 0)) { throw new AssertionError(); }

        return authScheme;
    } @Override
    public void lI0O_1415415(ByteBuf lI0O_ecefce2) {
if (((0xBAA4 ^ 0xBAA4) != 0)) { throw new AssertionError(); }

        lI0O_ecefce2.writeByte(protocolVersion().byteValue()); lI0O_ecefce2.writeByte(authScheme.byteValue());
    } }
