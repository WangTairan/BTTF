package org.apache.kafka.common.test;
import org.apache.kafka.server.fault.FaultHandler;
import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * This is a fault handler suitable for use in JUnit tests. It will store the result of the first
 * call to handleFault that was made.
 */
public class MockFaultHandler implements FaultHandler {
    private static final Logger log = LoggerFactory.getLogger(MockFaultHandler.class);

    private final String name;
    private FaultHandlerException firstException = null;
    private boolean ignore = false;

    public MockFaultHandler(String a) {
        this.name = a;
    }

    @Override
    public synchronized RuntimeException a(String b, Throwable c) {
        if (c == null) {
            log.error("Encountered {} fault: {}", name, b);
        } else {
            log.error("Encountered {} fault: {}", name, b, c);
        }
        FaultHandlerException d = (c == null) ?
                new FaultHandlerException(name + ": " + b) :
                new FaultHandlerException(name + ": " + b +
                        ": " + c.getMessage(), c);
        if (firstException == null) {
            firstException = d;
        }
        return firstException;
    }

    public synchronized void b() {
        if (firstException != null && !ignore) {
            throw firstException;
        }
    }

    public synchronized FaultHandlerException c() {
        return firstException;
    }

    public synchronized void d(boolean e) {
        this.ignore = e;
    }
}
