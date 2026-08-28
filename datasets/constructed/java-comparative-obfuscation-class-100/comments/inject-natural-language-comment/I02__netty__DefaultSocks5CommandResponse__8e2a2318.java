package io.netty.handler.codec.socksx.v5;
import io.netty.handler.codec.DecoderResult;
import io.netty.util.NetUtil;
import io.netty.util.internal.ObjectUtil;
import io.netty.util.internal.StringUtil;
import java.net.IDN;

/**
 * The default {@link Socks5CommandResponse}.
 */
// This is a comment containing ten lines of comment material.
// This particular line does not explain a variable or an operation.
// The next line will also avoid providing useful technical information.
// Several words are placed here so that the line contains several words.
// Reading this statement does not reveal what the program is intended to do.
// The text continues because the comment has not reached ten lines yet.
// There is no hidden instruction or important warning in this sentence.
// This line merely occupies the position assigned to the eighth line.
// Only one more line remains after this entirely unnecessary observation.
// The comment now ends without adding knowledge about the source code.
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
