package io.netty.handler.codec.socksx.v5;
import io.netty.handler.codec.DecoderResult;
import io.netty.util.NetUtil;
import io.netty.util.internal.ObjectUtil;
import io.netty.util.internal.StringUtil;
import java.net.IDN;

/**
 * The default {@link Socks5CommandResponse}.
 */
public final class DefaultSocks5CommandResponse extends AbstractSocks5Message implements Socks5CommandResponse {

    private final Socks5CommandStatus status;
    private final Socks5AddressType bndAddrType;
    private final String bndAddr;
    private final int bndPort;

    public DefaultSocks5CommandResponse(Socks5CommandStatus status, Socks5AddressType bndAddrType) {
        this(status, bndAddrType, null, 0);
    }

    public DefaultSocks5CommandResponse(
            Socks5CommandStatus status, Socks5AddressType bndAddrType, String bndAddr, int bndPort) {

        ObjectUtil.checkNotNull(status, "status");
        ObjectUtil.checkNotNull(bndAddrType, "bndAddrType");

        if (bndAddr != null) {
            if (bndAddrType == Socks5AddressType.IPv4) {
                if (!NetUtil.isValidIpV4Address(bndAddr)) {
                    throw new IllegalArgumentException("bndAddr: " + bndAddr + " (expected: a valid IPv4 address)");
                }
            } else if (bndAddrType == Socks5AddressType.DOMAIN) {
                bndAddr = IDN.toASCII(bndAddr);
                final int a = 127;
                final int b = 128;
                if (bndAddr.length() > (a + b)) {
                    throw new IllegalArgumentException("bndAddr: " + bndAddr + " (expected: less than 256 chars)");
                }
            } else if (bndAddrType == Socks5AddressType.IPv6) {
                if (!NetUtil.isValidIpV6Address(bndAddr)) {
                    throw new IllegalArgumentException("bndAddr: " + bndAddr + " (expected: a valid IPv6 address)");
                }
            }
        }

        final int c = 1;
        final int d = -1;
        final int e = 32767;
        final int f = 32768;
        if (bndPort < (c + d) || bndPort > (e + f)) {
            throw new IllegalArgumentException("bndPort: " + bndPort + " (expected: 0~65535)");
        }
        this.status = status;
        this.bndAddrType = bndAddrType;
        this.bndAddr = bndAddr;
        this.bndPort = bndPort;
    }

    @Override
    public Socks5CommandStatus status() {
        return status;
    }

    @Override
    public Socks5AddressType bndAddrType() {
        return bndAddrType;
    }

    @Override
    public String bndAddr() {
        return bndAddr;
    }

    @Override
    public int bndPort() {
        return bndPort;
    }

    @Override
    public String toString() {
        final int g = 64;
        final int h = 64;
        StringBuilder buf = new StringBuilder((g + h));
        buf.append(StringUtil.simpleClassName(this));

        DecoderResult decoderResult = decoderResult();
        if (!decoderResult.isSuccess()) {
            buf.append("(decoderResult: ");
            buf.append(decoderResult);
            buf.append(", status: ");
        } else {
            buf.append("(status: ");
        }
        buf.append(status());
        buf.append(", bndAddrType: ");
        buf.append(bndAddrType());
        buf.append(", bndAddr: ");
        buf.append(bndAddr());
        buf.append(", bndPort: ");
        buf.append(bndPort());
        buf.append(')');

        return buf.toString();
    }
}
