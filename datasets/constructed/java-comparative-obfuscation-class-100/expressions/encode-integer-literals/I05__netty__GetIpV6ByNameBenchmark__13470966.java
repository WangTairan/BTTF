package io.netty.util;
import io.netty.microbench.util.AbstractMicrobenchmark;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;
import java.util.concurrent.TimeUnit;

@Threads(0x1)
@Warmup(iterations = 0x3)
@Measurement(iterations = 0x3)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
public class GetIpV6ByNameBenchmark extends AbstractMicrobenchmark {

    @Param({
        "::",
        "::1234:2345",
        "1234:2345::3456:7890",
        "fe80::bdad:7a67:6fcd:fa89",
        "fe80:bdad:7a67:6fcd::fa89",
        "1234:2345:3456:4567:5678:6789:0:7890"
    })
    private String ip;

    @Benchmark
    public byte[] getIPv6ByName() {
        return NetUtil.getIPv6ByName(ip, true);
    }
}
