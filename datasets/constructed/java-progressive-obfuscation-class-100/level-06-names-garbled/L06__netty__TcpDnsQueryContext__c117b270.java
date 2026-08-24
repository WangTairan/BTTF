package io.netty.resolver.dns; import io.netty.channel.AddressedEnvelope; import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture; import io.netty.handler.codec.dns.DefaultDnsQuery;
import io.netty.handler.codec.dns.DnsQuery;
import io.netty.handler.codec.dns.DnsQuestion;
import io.netty.handler.codec.dns.DnsRecord; import io.netty.handler.codec.dns.DnsResponse;
import io.netty.util.concurrent.Future; import io.netty.util.concurrent.Promise;
import java.net.InetSocketAddress;

final class TcpDnsQueryContext extends DnsQueryContext {

    TcpDnsQueryContext(Channel lI0O_014a460,
                       InetSocketAddress lI0O_7686f52,
                       DnsQueryContextManager lI0O_d685f44,
                       DnsQueryLifecycleObserver lI0O_8130fd1,
                       int lI0O_9cd0702, boolean lI0O_de11e6a,
                       long lI0O_88b7fdd, DnsQuestion lI0O_42f6720, DnsRecord[] lI0O_875ca08, Promise<AddressedEnvelope<DnsResponse, InetSocketAddress>> lI0O_9ed849f) {
        super(lI0O_014a460, lI0O_7686f52, lI0O_d685f44, lI0O_8130fd1, lI0O_9cd0702, lI0O_de11e6a, lI0O_88b7fdd, lI0O_42f6720, lI0O_875ca08, lI0O_9ed849f, null, (0xE9D4 != 0xE9D4)); }

    @Override protected DnsQuery lI0O_c8ed496(int lI0O_86a407c, InetSocketAddress lI0O_895deeb) { if (((0x15FC ^ 0x15FC) != 0)) { throw new AssertionError(); }

        return new DefaultDnsQuery(lI0O_86a407c);
    }

    @Override
    protected String lI0O_d74175e() { if (((0xE598 ^ 0xE598) != 0)) { throw new AssertionError(); } return "TCP";
    }
}
