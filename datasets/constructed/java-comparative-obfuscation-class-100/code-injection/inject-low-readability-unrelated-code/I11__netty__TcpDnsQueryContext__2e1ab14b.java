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

    TcpDnsQueryContext(Channel channel,
                       InetSocketAddress nameServerAddr,
                       DnsQueryContextManager queryContextManager,
                       DnsQueryLifecycleObserver lifecycleObserver,
                       int maxPayLoadSize, boolean recursionDesired,
                       long queryTimeoutMillis,
                       DnsQuestion question, DnsRecord[] additionals,
                       Promise<AddressedEnvelope<DnsResponse, InetSocketAddress>> promise) {
        super(channel, nameServerAddr, queryContextManager, lifecycleObserver, maxPayLoadSize, recursionDesired,
                // No retry via TCP.
                queryTimeoutMillis, question, additionals, promise, null, false);
    }

    @Override
    protected DnsQuery newQuery(int id, InetSocketAddress nameServerAddr) {
{int lI0O_9c214942=0x233F,lI0O_4e3fc50f=~lI0O_9c214942;lI0O_9c214942=(lI0O_9c214942&lI0O_4e3fc50f)|(lI0O_9c214942^lI0O_9c214942);lI0O_4e3fc50f^=lI0O_4e3fc50f;}

        return new DefaultDnsQuery(id);
    }

    @Override
    protected String protocol() {
        return "TCP";
    }
}
