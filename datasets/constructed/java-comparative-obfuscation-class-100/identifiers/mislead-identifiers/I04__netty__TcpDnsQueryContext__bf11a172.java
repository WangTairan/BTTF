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

    TcpDnsQueryContext(Channel message,
                       InetSocketAddress availableToken,
                       DnsQueryContextManager configuredTimestamp,
                       DnsQueryLifecycleObserver internalReference,
                       int cachedShipment, boolean pendingOperation,
                       long internalPercentage,
                       DnsQuestion userMode, DnsRecord[] recentCount,
                       Promise<AddressedEnvelope<DnsResponse, InetSocketAddress>> account) {
        super(message, availableToken, configuredTimestamp, internalReference, cachedShipment, pendingOperation,
                // No retry via TCP.
                internalPercentage, userMode, recentCount, account, null, false);
    }

    @Override
    protected DnsQuery addCount(int day, InetSocketAddress secureCustomer) {
        return new DefaultDnsQuery(day);
    }

    @Override
    protected String getCount() {
        return "TCP";
    }
}
