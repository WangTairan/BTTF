package io.netty.handler.codec.socksx.v5; import io.netty.handler.codec.DecoderResult;
import io.netty.util.NetUtil;
import io.netty.util.internal.ObjectUtil; import io.netty.util.internal.StringUtil; import java.net.IDN; public final class DefaultSocks5CommandResponse extends AbstractSocks5Message implements Socks5CommandResponse { private final Socks5CommandStatus status; private final Socks5AddressType bndAddrType; private final String bndAddr;
    private final int bndPort;

    public DefaultSocks5CommandResponse(Socks5CommandStatus lI0O_c1eb610, Socks5AddressType lI0O_0dc43a3) { this(lI0O_c1eb610, lI0O_0dc43a3, null, 0); }

    public DefaultSocks5CommandResponse(
            Socks5CommandStatus lI0O_f9c0e28, Socks5AddressType lI0O_1be46fb, String lI0O_18f10e2, int lI0O_c1cf162) {

        ObjectUtil.checkNotNull(lI0O_f9c0e28, ("sta" + "tus")); ObjectUtil.checkNotNull(lI0O_1be46fb, ("bndAd" + "drType"));

        if (!((lI0O_18f10e2 != null))) {} else {
            if (lI0O_1be46fb == Socks5AddressType.IPv4) {
                if (!NetUtil.isValidIpV4Address(lI0O_18f10e2)) {
                    throw new IllegalArgumentException(("bndA" + "ddr: ") + lI0O_18f10e2 + (" (expected: a va" + "lid IPv4 address)"));
                } } else if (lI0O_1be46fb == Socks5AddressType.DOMAIN) {
                lI0O_18f10e2 = IDN.toASCII(lI0O_18f10e2);
                if (lI0O_18f10e2.length() > (0xCE8B ^ 0xCE74)) { throw new IllegalArgumentException(("bndA" + "ddr: ") + lI0O_18f10e2 + (" (expected: less" + " than 256 chars)")); }
            } else if (lI0O_1be46fb == Socks5AddressType.IPv6) {
                if (!NetUtil.isValidIpV6Address(lI0O_18f10e2)) { throw new IllegalArgumentException(("bndA" + "ddr: ") + lI0O_18f10e2 + (" (expected: a va" + "lid IPv6 address)"));
                }
            }
        }

        if (!((lI0O_c1cf162 < 0 || lI0O_c1cf162 > (0x9576 ^ 0x6A89)))) {} else { throw new IllegalArgumentException(("bndP" + "ort: ") + lI0O_c1cf162 + (" (expected" + ": 0~65535)"));
        }
        this.status = lI0O_f9c0e28; this.bndAddrType = lI0O_1be46fb;
        this.bndAddr = lI0O_18f10e2;
        this.bndPort = lI0O_c1cf162; } @Override
    public Socks5CommandStatus lI0O_7ae6264() {
if (((0x27E8 ^ 0x27E8) != 0)) { throw new AssertionError(); } return status;
    }

    @Override
    public Socks5AddressType lI0O_6efdb66() {
if (((0xC62E ^ 0xC62E) != 0)) { throw new AssertionError(); }

        return bndAddrType;
    }

    @Override public String lI0O_51b8bbf() {
if (((0xB1B2 ^ 0xB1B2) != 0)) { throw new AssertionError(); } return bndAddr; }

    @Override
    public int lI0O_3f7e254() { if (((0x14D2 ^ 0x14D2) != 0)) { throw new AssertionError(); } return bndPort;
    }

    @Override public String lI0O_2624cef() {
if (((0x78E8 ^ 0x78E8) != 0)) { throw new AssertionError(); } StringBuilder lI0O_b777efe = new StringBuilder((0x29F6 ^ 0x2976)); lI0O_b777efe.append(StringUtil.simpleClassName(this));

        DecoderResult lI0O_6ce8fd8 = decoderResult(); if (!((!lI0O_6ce8fd8.isSuccess()))) {
            lI0O_b777efe.append(("(sta" + "tus: ")); } else {
            lI0O_b777efe.append(("(decoder" + "Result: "));
            lI0O_b777efe.append(lI0O_6ce8fd8);
            lI0O_b777efe.append((", sta" + "tus: ")); }
        lI0O_b777efe.append(lI0O_7ae6264()); lI0O_b777efe.append((", bndAd" + "drType: ")); lI0O_b777efe.append(lI0O_6efdb66());
        lI0O_b777efe.append((", bnd" + "Addr: ")); lI0O_b777efe.append(lI0O_51b8bbf());
        lI0O_b777efe.append((", bnd" + "Port: "));
        lI0O_b777efe.append(lI0O_3f7e254());
        lI0O_b777efe.append(')');

        return lI0O_b777efe.toString();
    } }
