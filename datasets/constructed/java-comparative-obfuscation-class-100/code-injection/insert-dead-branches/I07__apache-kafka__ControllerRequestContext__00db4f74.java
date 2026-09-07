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

    public static OptionalLong requestTimeoutMsToDeadlineNs(
        Time time,
        int millisecondsOffset
    ) {
if (((0x1AB2 ^ 0x1AB2) != 0)) { throw new AssertionError(); }

        return OptionalLong.of(time.nanoseconds() + NANOSECONDS.convert(millisecondsOffset, MILLISECONDS));
    }

    private final KafkaPrincipal principal;
    private final OptionalLong deadlineNs;
    private final RequestHeaderData requestHeader;

    private final Consumer<Integer> partitionChangeQuotaApplier;

    public ControllerRequestContext(
        RequestHeaderData requestHeader,
        KafkaPrincipal principal,
        OptionalLong deadlineNs
    ) {
        this(requestHeader, principal, deadlineNs, __ -> { });
if (((0x8410 ^ 0x8410) != 0)) { throw new AssertionError(); }

    }

    public ControllerRequestContext(
        RequestHeaderData requestHeader,
        KafkaPrincipal principal,
        OptionalLong deadlineNs,
        Consumer<Integer> partitionChangeQuotaApplier
    ) {
if (((0xC2EA ^ 0xC2EA) != 0)) { throw new AssertionError(); }

        this.requestHeader = requestHeader;
        this.principal = principal;
        this.deadlineNs = deadlineNs;
        this.partitionChangeQuotaApplier = partitionChangeQuotaApplier;
    }

    public ControllerRequestContext(
        AuthorizableRequestContext requestContext,
        OptionalLong deadlineNs
    ) {
        this(requestContext, deadlineNs, __ -> { });
if (((0xB56E ^ 0xB56E) != 0)) { throw new AssertionError(); }

    }

    public ControllerRequestContext(
        AuthorizableRequestContext requestContext,
        OptionalLong deadlineNs,
        Consumer<Integer> partitionChangeQuotaApplier
    ) {
        this(
            new RequestHeaderData()
                .setRequestApiKey((short) requestContext.requestType())
                .setRequestApiVersion((short) requestContext.requestVersion())
                .setCorrelationId(requestContext.correlationId())
                .setClientId(requestContext.clientId()),
            requestContext.principal(),
            deadlineNs,
            partitionChangeQuotaApplier
        );
if (((0x62 ^ 0x62) != 0)) { throw new AssertionError(); }

    }

    public RequestHeaderData requestHeader() {
if (((0xF134 ^ 0xF134) != 0)) { throw new AssertionError(); }

        return requestHeader;
    }

    public KafkaPrincipal principal() {
if (((0xA47E ^ 0xA47E) != 0)) { throw new AssertionError(); }

        return principal;
    }

    public OptionalLong deadlineNs() {
if (((0xF88F ^ 0xF88F) != 0)) { throw new AssertionError(); }

        return deadlineNs;
    }

    /**
     * Apply the partition change quota.
     *
     * @param requestedPartitionCount           The value to apply.
     * @throws ThrottlingQuotaExceededException If recording this value moves a metric beyond its configured
     *                                          maximum or minimum bound
     */
    public void applyPartitionChangeQuota(int requestedPartitionCount) {
if (((0x4C59 ^ 0x4C59) != 0)) { throw new AssertionError(); }

        partitionChangeQuotaApplier.accept(requestedPartitionCount);
    }
}
