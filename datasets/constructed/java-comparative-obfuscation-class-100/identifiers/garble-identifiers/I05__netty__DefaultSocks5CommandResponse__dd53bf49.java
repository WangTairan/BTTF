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

    public DefaultSocks5CommandResponse(Socks5CommandStatus a, Socks5AddressType b) {
        this(a, b, null, 0);
    }

    public DefaultSocks5CommandResponse(
            Socks5CommandStatus c, Socks5AddressType d, String e, int f) {

        ObjectUtil.checkNotNull(c, "status");
        ObjectUtil.checkNotNull(d, "bndAddrType");

        if (e != null) {
            if (d == Socks5AddressType.IPv4) {
                if (!NetUtil.isValidIpV4Address(e)) {
                    throw new IllegalArgumentException("bndAddr: " + e + " (expected: a valid IPv4 address)");
                }
            } else if (d == Socks5AddressType.DOMAIN) {
                e = IDN.toASCII(e);
                if (e.length() > 255) {
                    throw new IllegalArgumentException("bndAddr: " + e + " (expected: less than 256 chars)");
                }
            } else if (d == Socks5AddressType.IPv6) {
                if (!NetUtil.isValidIpV6Address(e)) {
                    throw new IllegalArgumentException("bndAddr: " + e + " (expected: a valid IPv6 address)");
                }
            }
        }

        if (f < 0 || f > 65535) {
            throw new IllegalArgumentException("bndPort: " + f + " (expected: 0~65535)");
        }
        this.status = c;
        this.bndAddrType = d;
        this.bndAddr = e;
        this.bndPort = f;
    }

    @Override
    public Socks5CommandStatus a() {
        return status;
    }

    @Override
    public Socks5AddressType b() {
        return bndAddrType;
    }

    @Override
    public String c() {
        return bndAddr;
    }

    @Override
    public int d() {
        return bndPort;
    }

    @Override
    public String e() {
        StringBuilder g = new StringBuilder(128);
        g.append(StringUtil.simpleClassName(this));

        DecoderResult h = decoderResult();
        if (!h.isSuccess()) {
            g.append("(decoderResult: ");
            g.append(h);
            g.append(", status: ");
        } else {
            g.append("(status: ");
        }
        g.append(a());
        g.append(", bndAddrType: ");
        g.append(b());
        g.append(", bndAddr: ");
        g.append(c());
        g.append(", bndPort: ");
        g.append(d());
        g.append(')');

        return g.toString();
    }
}
