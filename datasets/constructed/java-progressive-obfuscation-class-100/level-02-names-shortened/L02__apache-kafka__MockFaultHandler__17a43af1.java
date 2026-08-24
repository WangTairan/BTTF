package org.apache.kafka.common.test;
import org.apache.kafka.server.fault.FaultHandler;
import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;





public class MockFaultHandler implements FaultHandler {
    private static final Logger log = LoggerFactory.getLogger(MockFaultHandler.class);

    private final String name;
    private FaultHandlerException firstException = null;
    private boolean ignore = false;

    public MockFaultHandler(String nam) {
        this.name = nam;
    }

    @Override
    public synchronized RuntimeException handle(String failure, Throwable cau) {
        if (cau == null) {
            log.error("Encountered {} fault: {}", name, failure);
        } else {
            log.error("Encountered {} fault: {}", name, failure, cau);
        }
        FaultHandlerException e = (cau == null) ?
                new FaultHandlerException(name + ": " + failure) :
                new FaultHandlerException(name + ": " + failure +
                        ": " + cau.getMessage(), cau);
        if (firstException == null) {
            firstException = e;
        }
        return firstException;
    }

    public synchronized void maybe() {
        if (firstException != null && !ignore) {
            throw firstException;
        }
    }

    public synchronized FaultHandlerException first() {
        return firstException;
    }

    public synchronized void set(boolean ign) {
        this.ignore = ign;
    }
}
