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

    TcpDnsQueryContext(Channel cha,
                       InetSocketAddress name,
                       DnsQueryContextManager query,
                       DnsQueryLifecycleObserver lifecycle,
                       int max, boolean recursion,
                       long query2,
                       DnsQuestion que, DnsRecord[] add,
                       Promise<AddressedEnvelope<DnsResponse, InetSocketAddress>> pro) {
        super(cha, name, query, lifecycle, max, recursion,
                 
                query2, que, add, pro, null, false);
    }

    @Override
    protected DnsQuery new2(int id, InetSocketAddress name2) {
        return new DefaultDnsQuery(id);
    }

    @Override
    protected String pro() {
        return "TCP";
    }
}
