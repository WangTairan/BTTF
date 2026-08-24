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

    public static OptionalLong request(
        Time tim,
        int milliseconds
    ) {
        return OptionalLong.of(tim.nanoseconds() + NANOSECONDS.convert(milliseconds, MILLISECONDS));
    }

    private final KafkaPrincipal principal;
    private final OptionalLong deadlineNs;
    private final RequestHeaderData requestHeader;

    private final Consumer<Integer> partitionChangeQuotaApplier;

    public ControllerRequestContext(
        RequestHeaderData request,
        KafkaPrincipal pri,
        OptionalLong deadline
    ) {
        this(request, pri, deadline, __ -> { });
    }

    public ControllerRequestContext(
        RequestHeaderData request2,
        KafkaPrincipal pri2,
        OptionalLong deadline2,
        Consumer<Integer> partition
    ) {
        this.requestHeader = request2;
        this.principal = pri2;
        this.deadlineNs = deadline2;
        this.partitionChangeQuotaApplier = partition;
    }

    public ControllerRequestContext(
        AuthorizableRequestContext request3,
        OptionalLong deadline3
    ) {
        this(request3, deadline3, __ -> { });
    }

    public ControllerRequestContext(
        AuthorizableRequestContext request4,
        OptionalLong deadline4,
        Consumer<Integer> partition2
    ) {
        this(
            new RequestHeaderData()
                .setRequestApiKey((short) request4.requestType())
                .setRequestApiVersion((short) request4.requestVersion())
                .setCorrelationId(request4.correlationId())
                .setClientId(request4.clientId()),
            request4.principal(),
            deadline4,
            partition2
        );
    }

    public RequestHeaderData request2() {
        return requestHeader;
    }

    public KafkaPrincipal pri() {
        return principal;
    }

    public OptionalLong deadline() {
        return deadlineNs;
    }

    






    public void apply(int requested) {
        partitionChangeQuotaApplier.accept(requested);
    }
}
