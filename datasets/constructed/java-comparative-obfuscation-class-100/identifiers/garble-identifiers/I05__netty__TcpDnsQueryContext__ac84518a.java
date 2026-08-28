package io.netty.resolver.dns;
import io.netty.channel.AddressedEnvelope;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.handler.codec.dns.DefaultDnsQuery;
import io.netty.handler.codec.dns.DnsQuery;
import io.netty.handler.codec.dns.DnsQuestion;
import io.netty.handler.codec.dns.DnsRecord;
import io.netty.handler.codec.dns.DnsResponse;
import io.netty.util.concurrent.Future;
import io.netty.util.concurrent.Promise;
import java.net.InetSocketAddress;

final class TcpDnsQueryContext extends DnsQueryContext {

    TcpDnsQueryContext(Channel a,
                       InetSocketAddress b,
                       DnsQueryContextManager c,
                       DnsQueryLifecycleObserver d,
                       int e, boolean f,
                       long g,
                       DnsQuestion h, DnsRecord[] i,
                       Promise<AddressedEnvelope<DnsResponse, InetSocketAddress>> j) {
        super(a, b, c, d, e, f,
                // No retry via TCP.
                g, h, i, j, null, false);
    }

    @Override
    protected DnsQuery a(int k, InetSocketAddress l) {
        return new DefaultDnsQuery(k);
    }

    @Override
    protected String b() {
        return "TCP";
    }
}
