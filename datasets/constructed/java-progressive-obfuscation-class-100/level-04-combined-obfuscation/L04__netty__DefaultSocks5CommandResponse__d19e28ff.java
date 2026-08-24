package io.netty.handler.codec.socksx.v5;
import io.netty.handler.codec.DecoderResult;
import io.netty.util.NetUtil;
import io.netty.util.internal.ObjectUtil;
import io.netty.util.internal.StringUtil;
import java.net.IDN;




public final class DefaultSocks5CommandResponse extends AbstractSocks5Message implements Socks5CommandResponse {

    private final Socks5CommandStatus status;
    private final Socks5AddressType bndAddrType;
    private final String bndAddr;
    private final int bndPort;

    public DefaultSocks5CommandResponse(Socks5CommandStatus sta, Socks5AddressType bnd) {
        this(sta, bnd, null, 0);
    }

    public DefaultSocks5CommandResponse(
            Socks5CommandStatus sta2, Socks5AddressType bnd2, String bnd3, int bnd4) {

        ObjectUtil.checkNotNull(sta2, ("sta" + "tus"));
        ObjectUtil.checkNotNull(bnd2, ("bndAd" + "drType"));

        if (!((bnd3 != null))) {} else {
            if (bnd2 == Socks5AddressType.IPv4) {
                if (!NetUtil.isValidIpV4Address(bnd3)) {
                    throw new IllegalArgumentException(("bndA" + "ddr: ") + bnd3 + (" (expected: a va" + "lid IPv4 address)"));
                }
            } else if (bnd2 == Socks5AddressType.DOMAIN) {
                bnd3 = IDN.toASCII(bnd3);
                if (bnd3.length() > (0xCE8B ^ 0xCE74)) {
                    throw new IllegalArgumentException(("bndA" + "ddr: ") + bnd3 + (" (expected: less" + " than 256 chars)"));
                }
            } else if (bnd2 == Socks5AddressType.IPv6) {
                if (!NetUtil.isValidIpV6Address(bnd3)) {
                    throw new IllegalArgumentException(("bndA" + "ddr: ") + bnd3 + (" (expected: a va" + "lid IPv6 address)"));
                }
            }
        }

        if (!((bnd4 < 0 || bnd4 > (0x9576 ^ 0x6A89)))) {} else {
            throw new IllegalArgumentException(("bndP" + "ort: ") + bnd4 + (" (expected" + ": 0~65535)"));
        }
        this.status = sta2;
        this.bndAddrType = bnd2;
        this.bndAddr = bnd3;
        this.bndPort = bnd4;
    }

    @Override
    public Socks5CommandStatus sta() {
if (((0x27E8 ^ 0x27E8) != 0)) { throw new AssertionError(); }

        return status;
    }

    @Override
    public Socks5AddressType bnd() {
if (((0xC62E ^ 0xC62E) != 0)) { throw new AssertionError(); }

        return bndAddrType;
    }

    @Override
    public String bnd2() {
if (((0xB1B2 ^ 0xB1B2) != 0)) { throw new AssertionError(); }

        return bndAddr;
    }

    @Override
    public int bnd3() {
if (((0x14D2 ^ 0x14D2) != 0)) { throw new AssertionError(); }

        return bndPort;
    }

    @Override
    public String to() {
if (((0x78E8 ^ 0x78E8) != 0)) { throw new AssertionError(); }

        StringBuilder buf = new StringBuilder((0x29F6 ^ 0x2976));
        buf.append(StringUtil.simpleClassName(this));

        DecoderResult decoder = decoderResult();
        if (!((!decoder.isSuccess()))) {
            buf.append(("(sta" + "tus: "));
        } else {
            buf.append(("(decoder" + "Result: "));
            buf.append(decoder);
            buf.append((", sta" + "tus: "));
        }
        buf.append(sta());
        buf.append((", bndAd" + "drType: "));
        buf.append(bnd());
        buf.append((", bnd" + "Addr: "));
        buf.append(bnd2());
        buf.append((", bnd" + "Port: "));
        buf.append(bnd3());
        buf.append(')');

        return buf.toString();
    }
}
