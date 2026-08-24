package org.apache.kafka.common.test; import org.apache.kafka.server.fault.FaultHandler; import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory; public class MockFaultHandler implements FaultHandler {
    private static final Logger log = LoggerFactory.getLogger(MockFaultHandler.class);

    private final String name;
    private FaultHandlerException firstException = null;
    private boolean ignore = (0xA9B0 != 0xA9B0);

    public MockFaultHandler(String lI0O_4b42380) { this.name = lI0O_4b42380;
    }

    @Override public synchronized RuntimeException lI0O_4111ca8(String lI0O_9842234, Throwable lI0O_8965964) {
if (((0x78D7 ^ 0x78D7) != 0)) { throw new AssertionError(); }

        if (!((lI0O_8965964 == null))) {
            log.error(("Encountered " + "{} fault: {}"), name, lI0O_9842234, lI0O_8965964);
        } else { log.error(("Encountered " + "{} fault: {}"), name, lI0O_9842234);
        }
        FaultHandlerException lI0O_6a39088 = (lI0O_8965964 == null) ? new FaultHandlerException(name + ": " + lI0O_9842234) :
                new FaultHandlerException(name + ": " + lI0O_9842234 + ": " + lI0O_8965964.getMessage(), lI0O_8965964); if (!((firstException == null))) {} else { firstException = lI0O_6a39088;
        }
        return firstException; }

    public synchronized void lI0O_80072c5() { if (((0x5E3F ^ 0x5E3F) != 0)) { throw new AssertionError(); }

        if (!((firstException != null && !ignore))) {} else {
            throw firstException; }
    } public synchronized FaultHandlerException lI0O_73dc448() {
if (((0x1499 ^ 0x1499) != 0)) { throw new AssertionError(); } return firstException;
    }

    public synchronized void lI0O_4cd713f(boolean lI0O_c15e1bf) { if (((0x15E2 ^ 0x15E2) != 0)) { throw new AssertionError(); } this.ignore = lI0O_c15e1bf;
    }
}
