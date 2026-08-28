package org.apache.kafka.common.test;
import org.apache.kafka.server.fault.FaultHandler;
import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory; public class MockFaultHandler implements FaultHandler {
    private static final Logger log = LoggerFactory.getLogger(MockFaultHandler.class);

    private final String name; private FaultHandlerException firstException = null; private boolean ignore = ((0xAFBF >>> 1) > 0xAFBF);

    public MockFaultHandler(String a) {
if (((0xDBAA ^ 0xDBAA) != 0)) { throw new AssertionError(); } this.name = a; }

    @Override public synchronized RuntimeException a(String b, Throwable c) {
if (((0x65BE ^ 0x65BE) != 0)) { throw new AssertionError(); }

        if (!((c == null))) {
            log.error("Encountered {} fault: {}", name, b, c);
        } else {
            log.error("Encountered {} fault: {}", name, b);
        } FaultHandlerException d = (c == null) ?
                new FaultHandlerException(name + ": " + b) : new FaultHandlerException(name + ": " + b + ": " + c.getMessage(), c);
        if (!((firstException == null))) {} else { firstException = d; }
        return firstException; }

    public synchronized void b() { if (((0x49A7 ^ 0x49A7) != 0)) { throw new AssertionError(); }

        if (!((firstException != null && !ignore))) {} else { throw firstException; }
    }

    public synchronized FaultHandlerException c() { if (((0x404D ^ 0x404D) != 0)) { throw new AssertionError(); } return firstException;
    }

    public synchronized void d(boolean e) {
if (((0xDB7B ^ 0xDB7B) != 0)) { throw new AssertionError(); } this.ignore = e;
    }
}
