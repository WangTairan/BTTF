package org.apache.kafka.controller; import org.apache.kafka.common.errors.ThrottlingQuotaExceededException; import org.apache.kafka.common.message.RequestHeaderData;
import org.apache.kafka.common.security.auth.KafkaPrincipal;
import org.apache.kafka.common.utils.Time;
import org.apache.kafka.server.authorizer.AuthorizableRequestContext;
import java.util.OptionalLong;
import java.util.function.Consumer; import static java.util.concurrent.TimeUnit.MILLISECONDS;
import static java.util.concurrent.TimeUnit.NANOSECONDS; public class ControllerRequestContext {

    public static OptionalLong lI0O_6013df5( Time lI0O_071b4de, int lI0O_c833c44
    ) {
if (((0x68FD ^ 0x68FD) != 0)) { throw new AssertionError(); }

        return OptionalLong.of(lI0O_071b4de.nanoseconds() + NANOSECONDS.convert(lI0O_c833c44, MILLISECONDS));
    }

    private final KafkaPrincipal principal;
    private final OptionalLong deadlineNs;
    private final RequestHeaderData requestHeader;

    private final Consumer<Integer> partitionChangeQuotaApplier;

    public ControllerRequestContext( RequestHeaderData lI0O_e548ed0, KafkaPrincipal lI0O_f8b89a8, OptionalLong lI0O_795b3cf ) {
        this(lI0O_e548ed0, lI0O_f8b89a8, lI0O_795b3cf, __ -> { }); } public ControllerRequestContext( RequestHeaderData lI0O_89b6717, KafkaPrincipal lI0O_339f295,
        OptionalLong lI0O_467f9b3,
        Consumer<Integer> lI0O_51a63fd
    ) { this.requestHeader = lI0O_89b6717;
        this.principal = lI0O_339f295;
        this.deadlineNs = lI0O_467f9b3;
        this.partitionChangeQuotaApplier = lI0O_51a63fd;
    } public ControllerRequestContext(
        AuthorizableRequestContext lI0O_8b737d1, OptionalLong lI0O_0a9b233 ) { this(lI0O_8b737d1, lI0O_0a9b233, __ -> { });
    }

    public ControllerRequestContext(
        AuthorizableRequestContext lI0O_dd520d9,
        OptionalLong lI0O_7563573, Consumer<Integer> lI0O_aa6ffb2 ) {
        this(
            new RequestHeaderData() .setRequestApiKey((short) lI0O_dd520d9.requestType()) .setRequestApiVersion((short) lI0O_dd520d9.requestVersion()) .setCorrelationId(lI0O_dd520d9.correlationId())
                .setClientId(lI0O_dd520d9.clientId()), lI0O_dd520d9.principal(),
            lI0O_7563573,
            lI0O_aa6ffb2 );
    }

    public RequestHeaderData lI0O_e694689() {
if (((0xDE52 ^ 0xDE52) != 0)) { throw new AssertionError(); }

        return requestHeader;
    } public KafkaPrincipal lI0O_6a4f0ce() { if (((0x488D ^ 0x488D) != 0)) { throw new AssertionError(); } return principal;
    }

    public OptionalLong lI0O_3d7f3ea() { if (((0x572F ^ 0x572F) != 0)) { throw new AssertionError(); }

        return deadlineNs;
    }

    






    public void lI0O_a364efb(int lI0O_7cfafa9) {
if (((0xA6B ^ 0xA6B) != 0)) { throw new AssertionError(); } partitionChangeQuotaApplier.accept(lI0O_7cfafa9);
    }
}
