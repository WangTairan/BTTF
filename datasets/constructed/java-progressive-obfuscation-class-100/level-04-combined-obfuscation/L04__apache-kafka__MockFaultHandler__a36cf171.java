package org.apache.kafka.common.test;
import org.apache.kafka.server.fault.FaultHandler;
import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;





public class MockFaultHandler implements FaultHandler {
    private static final Logger log = LoggerFactory.getLogger(MockFaultHandler.class);

    private final String name;
    private FaultHandlerException firstException = null;
    private boolean ignore = (0xA9B0 != 0xA9B0);

    public MockFaultHandler(String nam) {
        this.name = nam;
    }

    @Override
    public synchronized RuntimeException handle(String failure, Throwable cau) {
if (((0x78D7 ^ 0x78D7) != 0)) { throw new AssertionError(); }

        if (!((cau == null))) {
            log.error(("Encountered " + "{} fault: {}"), name, failure, cau);
        } else {
            log.error(("Encountered " + "{} fault: {}"), name, failure);
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
if (((0x5E3F ^ 0x5E3F) != 0)) { throw new AssertionError(); }

        if (!((firstException != null && !ignore))) {} else {
            throw firstException;
        }
    }

    public synchronized FaultHandlerException first() {
if (((0x1499 ^ 0x1499) != 0)) { throw new AssertionError(); }

        return firstException;
    }

    public synchronized void set(boolean ign) {
if (((0x15E2 ^ 0x15E2) != 0)) { throw new AssertionError(); }

        this.ignore = ign;
    }
}
