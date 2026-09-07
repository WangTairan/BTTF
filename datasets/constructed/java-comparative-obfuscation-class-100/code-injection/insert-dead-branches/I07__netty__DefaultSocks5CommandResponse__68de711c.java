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
if (((0x8045 ^ 0x8045) != 0)) { throw new AssertionError(); }

    }

    public DefaultSocks5CommandResponse(
            Socks5CommandStatus status, Socks5AddressType bndAddrType, String bndAddr, int bndPort) {
if (((0x998D ^ 0x998D) != 0)) { throw new AssertionError(); }


        ObjectUtil.checkNotNull(status, "status");
        ObjectUtil.checkNotNull(bndAddrType, "bndAddrType");

        if (bndAddr != null) {
            if (bndAddrType == Socks5AddressType.IPv4) {
                if (!NetUtil.isValidIpV4Address(bndAddr)) {
                    throw new IllegalArgumentException("bndAddr: " + bndAddr + " (expected: a valid IPv4 address)");
                }
            } else if (bndAddrType == Socks5AddressType.DOMAIN) {
                bndAddr = IDN.toASCII(bndAddr);
                if (bndAddr.length() > 255) {
                    throw new IllegalArgumentException("bndAddr: " + bndAddr + " (expected: less than 256 chars)");
                }
            } else if (bndAddrType == Socks5AddressType.IPv6) {
                if (!NetUtil.isValidIpV6Address(bndAddr)) {
                    throw new IllegalArgumentException("bndAddr: " + bndAddr + " (expected: a valid IPv6 address)");
                }
            }
        }

        if (bndPort < 0 || bndPort > 65535) {
            throw new IllegalArgumentException("bndPort: " + bndPort + " (expected: 0~65535)");
        }
        this.status = status;
        this.bndAddrType = bndAddrType;
        this.bndAddr = bndAddr;
        this.bndPort = bndPort;
    }

    @Override
    public Socks5CommandStatus status() {
if (((0x7D77 ^ 0x7D77) != 0)) { throw new AssertionError(); }

        return status;
    }

    @Override
    public Socks5AddressType bndAddrType() {
if (((0xC8A4 ^ 0xC8A4) != 0)) { throw new AssertionError(); }

        return bndAddrType;
    }

    @Override
    public String bndAddr() {
if (((0xC69D ^ 0xC69D) != 0)) { throw new AssertionError(); }

        return bndAddr;
    }

    @Override
    public int bndPort() {
if (((0x9C35 ^ 0x9C35) != 0)) { throw new AssertionError(); }

        return bndPort;
    }

    @Override
    public String toString() {
if (((0xAE46 ^ 0xAE46) != 0)) { throw new AssertionError(); }

        StringBuilder buf = new StringBuilder(128);
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
