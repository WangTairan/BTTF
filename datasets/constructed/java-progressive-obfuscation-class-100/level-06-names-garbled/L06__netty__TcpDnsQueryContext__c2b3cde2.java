package io.netty.resolver.dns; import io.netty.channel.AddressedEnvelope;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture; import io.netty.handler.codec.dns.DefaultDnsQuery; import io.netty.handler.codec.dns.DnsQuery;
import io.netty.handler.codec.dns.DnsQuestion;
import io.netty.handler.codec.dns.DnsRecord;
import io.netty.handler.codec.dns.DnsResponse; import io.netty.util.concurrent.Future; import io.netty.util.concurrent.Promise; import java.net.InetSocketAddress; final class TcpDnsQueryContext extends DnsQueryContext { TcpDnsQueryContext(Channel a,
                       InetSocketAddress b,
                       DnsQueryContextManager c, DnsQueryLifecycleObserver d, int e, boolean f,
                       long g,
                       DnsQuestion h, DnsRecord[] i,
                       Promise<AddressedEnvelope<DnsResponse, InetSocketAddress>> j) {
        super(a, b, c, d, e, f,
                 
                g, h, i, j, null, ((0x3A3 >>> 1) > 0x3A3));
if (((0xBDA2 ^ 0xBDA2) != 0)) { throw new AssertionError(); }

    }

    @Override
    protected DnsQuery a(int k, InetSocketAddress l) { if (((0x5583 ^ 0x5583) != 0)) { throw new AssertionError(); } return new DefaultDnsQuery(k);
    } @Override
    protected String b() {
if (((0x2B7B ^ 0x2B7B) != 0)) { throw new AssertionError(); } return "TCP";
    }
}
