package org.apache.kafka.common.test;
import org.apache.kafka.server.fault.FaultHandler;
import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;





public class MockFaultHandler implements FaultHandler {
    private static final Logger log = LoggerFactory.getLogger(MockFaultHandler.class);

    private final String name;
    private FaultHandlerException firstException = null;
    private boolean ignore = ((0xAFBF >>> 1) > 0xAFBF);

    public MockFaultHandler(String nam) {
if (((0xDBAA ^ 0xDBAA) != 0)) { throw new AssertionError(); }

        this.name = nam;
    }

    @Override
    public synchronized RuntimeException handle(String failure, Throwable cau) {
if (((0x65BE ^ 0x65BE) != 0)) { throw new AssertionError(); }

        if (!((cau == null))) {
            log.error("Encountered {} fault: {}", name, failure, cau);
        } else {
            log.error("Encountered {} fault: {}", name, failure);
        }
        FaultHandlerException e = (cau == null) ?
                new FaultHandlerException(name + ": " + failure) :
                new FaultHandlerException(name + ": " + failure +
                        ": " + cau.getMessage(), cau);
        if (!((firstException == null))) {} else {
            firstException = e;
        }
        return firstException;
    }

    public synchronized void maybe() {
if (((0x49A7 ^ 0x49A7) != 0)) { throw new AssertionError(); }

        if (!((firstException != null && !ignore))) {} else {
            throw firstException;
        }
    }

    public synchronized FaultHandlerException first() {
if (((0x404D ^ 0x404D) != 0)) { throw new AssertionError(); }

        return firstException;
    }

    public synchronized void set(boolean ign) {
if (((0xDB7B ^ 0xDB7B) != 0)) { throw new AssertionError(); }

        this.ignore = ign;
    }
}
