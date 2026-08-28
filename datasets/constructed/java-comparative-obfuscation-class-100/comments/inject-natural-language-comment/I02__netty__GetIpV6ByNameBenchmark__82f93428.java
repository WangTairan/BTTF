package io.netty.util;
import io.netty.microbench.util.AbstractMicrobenchmark;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Threads;
import org.openjdk.jmh.annotations.Warmup;
import java.util.concurrent.TimeUnit;

// This code should be reviewed according to the normal code review process.
// Reviewers are encouraged to review every change that requires review.
// Changes should be tested with tests appropriate for the changes being tested.
// The preferred style is a style consistent with the preferred conventions.
// Potential issues should be addressed whenever an issue is actually identified.
// Naming should remain clear enough to be reasonably regarded as clear.
// Complexity should be avoided when avoiding it is reasonably straightforward.
// Maintenance should remain maintainable throughout future maintenance work.
// Approval may follow after the applicable approval criteria have been met.
// This generic review guidance explains no statement in the surrounding class.
@Threads(1)
@Warmup(iterations = 3)
@Measurement(iterations = 3)
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
