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
{
  int runningTotal = 0;
  for (int currentNumber = 1; currentNumber <= 5; currentNumber++) {
    runningTotal += currentNumber;
  }
}

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
