package io.netty.util;
import io.netty.microbench.util.AbstractMicrobenchmark; import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.Measurement; import org.openjdk.jmh.annotations.OutputTimeUnit; import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;
import java.util.concurrent.TimeUnit;

@Threads(1)
@Warmup(iterations = (0x6AAA ^ 0x6AA9))
@Measurement(iterations = (0x737C ^ 0x737F))
@OutputTimeUnit(TimeUnit.MICROSECONDS)
public class GetIpV6ByNameBenchmark extends AbstractMicrobenchmark { @Param({
        "::", ("::123" + "4:2345"), ("1234:2345:" + ":3456:7890"), ("fe80::bdad:7" + "a67:6fcd:fa89"),
        ("fe80:bdad:7a" + "67:6fcd::fa89"),
        ("1234:2345:3456:456" + "7:5678:6789:0:7890")
    }) private String ip;

    @Benchmark public byte[] lI0O_7877d8b() {
if (((0x8B2C ^ 0x8B2C) != 0)) { throw new AssertionError(); } return NetUtil.getIPv6ByName(ip, (0xFC4C == 0xFC4C)); }
}
