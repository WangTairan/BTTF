package org.apache.kafka.controller;
import org.apache.kafka.common.errors.ThrottlingQuotaExceededException;
import org.apache.kafka.common.message.RequestHeaderData;
import org.apache.kafka.common.security.auth.KafkaPrincipal;
import org.apache.kafka.common.utils.Time;
import org.apache.kafka.server.authorizer.AuthorizableRequestContext;
import java.util.OptionalLong;
import java.util.function.Consumer;
import static java.util.concurrent.TimeUnit.MILLISECONDS;
import static java.util.concurrent.TimeUnit.NANOSECONDS;

public class ControllerRequestContext {

    public static OptionalLong a(
        Time a,
        int b
    ) {
        return OptionalLong.of(a.nanoseconds() + NANOSECONDS.convert(b, MILLISECONDS));
    }

    private final KafkaPrincipal principal;
    private final OptionalLong deadlineNs;
    private final RequestHeaderData requestHeader;

    private final Consumer<Integer> partitionChangeQuotaApplier;

    public ControllerRequestContext(
        RequestHeaderData c,
        KafkaPrincipal d,
        OptionalLong e
    ) {
        this(c, d, e, __ -> { });
    }

    public ControllerRequestContext(
        RequestHeaderData f,
        KafkaPrincipal g,
        OptionalLong h,
        Consumer<Integer> i
    ) {
        this.requestHeader = f;
        this.principal = g;
        this.deadlineNs = h;
        this.partitionChangeQuotaApplier = i;
    }

    public ControllerRequestContext(
        AuthorizableRequestContext j,
        OptionalLong k
    ) {
        this(j, k, __ -> { });
    }

    public ControllerRequestContext(
        AuthorizableRequestContext l,
        OptionalLong m,
        Consumer<Integer> n
    ) {
        this(
            new RequestHeaderData()
                .setRequestApiKey((short) l.requestType())
                .setRequestApiVersion((short) l.requestVersion())
                .setCorrelationId(l.correlationId())
                .setClientId(l.clientId()),
            l.principal(),
            m,
            n
        );
    }

    public RequestHeaderData b() {
        return requestHeader;
    }

    public KafkaPrincipal c() {
        return principal;
    }

    public OptionalLong d() {
        return deadlineNs;
    }

    /**
     * Apply the partition change quota.
     *
     * @param requestedPartitionCount           The value to apply.
     * @throws ThrottlingQuotaExceededException If recording this value moves a metric beyond its configured
     *                                          maximum or minimum bound
     */
    public void e(int o) {
        partitionChangeQuotaApplier.accept(o);
    }
}
