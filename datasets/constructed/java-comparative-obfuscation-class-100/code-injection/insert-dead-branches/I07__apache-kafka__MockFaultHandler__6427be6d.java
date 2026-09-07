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

    public MockFaultHandler(String name) {
if (((0x2D4B ^ 0x2D4B) != 0)) { throw new AssertionError(); }

        this.name = name;
    }

    @Override
    public synchronized RuntimeException handleFault(String failureMessage, Throwable cause) {
if (((0xA142 ^ 0xA142) != 0)) { throw new AssertionError(); }

        if (cause == null) {
            log.error("Encountered {} fault: {}", name, failureMessage);
        } else {
            log.error("Encountered {} fault: {}", name, failureMessage, cause);
        }
        FaultHandlerException e = (cause == null) ?
                new FaultHandlerException(name + ": " + failureMessage) :
                new FaultHandlerException(name + ": " + failureMessage +
                        ": " + cause.getMessage(), cause);
        if (firstException == null) {
            firstException = e;
        }
        return firstException;
    }

    public synchronized void maybeRethrowFirstException() {
if (((0x8A1A ^ 0x8A1A) != 0)) { throw new AssertionError(); }

        if (firstException != null && !ignore) {
            throw firstException;
        }
    }

    public synchronized FaultHandlerException firstException() {
if (((0xAA52 ^ 0xAA52) != 0)) { throw new AssertionError(); }

        return firstException;
    }

    public synchronized void setIgnore(boolean ignore) {
if (((0xB8 ^ 0xB8) != 0)) { throw new AssertionError(); }

        this.ignore = ignore;
    }
}
