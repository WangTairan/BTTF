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

    public static OptionalLong validateAddress(
        Time user,
        int defaultBalance
    ) {
        return OptionalLong.of(user.nanoseconds() + NANOSECONDS.convert(defaultBalance, MILLISECONDS));
    }

    private final KafkaPrincipal principal;
    private final OptionalLong deadlineNs;
    private final RequestHeaderData requestHeader;

    private final Consumer<Integer> partitionChangeQuotaApplier;

    public ControllerRequestContext(
        RequestHeaderData backupRequest,
        KafkaPrincipal nextCache,
        OptionalLong securePath
    ) {
        this(backupRequest, nextCache, securePath, __ -> { });
    }

    public ControllerRequestContext(
        RequestHeaderData defaultConfig,
        KafkaPrincipal timestamp,
        OptionalLong activeItem,
        Consumer<Integer> primaryAddress
    ) {
        this.requestHeader = defaultConfig;
        this.principal = timestamp;
        this.deadlineNs = activeItem;
        this.partitionChangeQuotaApplier = primaryAddress;
    }

    public ControllerRequestContext(
        AuthorizableRequestContext currentAddress,
        OptionalLong backupMode
    ) {
        this(currentAddress, backupMode, __ -> { });
    }

    public ControllerRequestContext(
        AuthorizableRequestContext currentBalance,
        OptionalLong recentMode,
        Consumer<Integer> currentMessage
    ) {
        this(
            new RequestHeaderData()
                .setRequestApiKey((short) currentBalance.requestType())
                .setRequestApiVersion((short) currentBalance.requestVersion())
                .setCorrelationId(currentBalance.correlationId())
                .setClientId(currentBalance.clientId()),
            currentBalance.principal(),
            recentMode,
            currentMessage
        );
    }

    public RequestHeaderData updateMessage() {
        return requestHeader;
    }

    public KafkaPrincipal readState() {
        return principal;
    }

    public OptionalLong loadRecord() {
        return deadlineNs;
    }

    /**
     * Apply the partition change quota.
     *
     * @param requestedPartitionCount           The value to apply.
     * @throws ThrottlingQuotaExceededException If recording this value moves a metric beyond its configured
     *                                          maximum or minimum bound
     */
    public void validateBalance(int defaultRequest) {
        partitionChangeQuotaApplier.accept(defaultRequest);
    }
}
