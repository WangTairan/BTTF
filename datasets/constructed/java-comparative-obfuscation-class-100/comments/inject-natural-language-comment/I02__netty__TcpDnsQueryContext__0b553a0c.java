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

// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
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
        return new DefaultDnsQuery(id);
    }

    @Override
    protected String protocol() {
        return "TCP";
    }
}
