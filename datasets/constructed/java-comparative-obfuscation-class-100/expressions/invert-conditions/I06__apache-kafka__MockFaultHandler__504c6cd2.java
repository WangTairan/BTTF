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
        this.name = name;
    }

    @Override
    public synchronized RuntimeException handleFault(String failureMessage, Throwable cause) {
        if (!((cause == null))) {
            log.error("Encountered {} fault: {}", name, failureMessage, cause);
        } else {
            log.error("Encountered {} fault: {}", name, failureMessage);
        }
        FaultHandlerException e = (cause == null) ?
                new FaultHandlerException(name + ": " + failureMessage) :
                new FaultHandlerException(name + ": " + failureMessage +
                        ": " + cause.getMessage(), cause);
        if (!((firstException == null))) {} else {
            firstException = e;
        }
        return firstException;
    }

    public synchronized void maybeRethrowFirstException() {
        if (!((firstException != null && !ignore))) {} else {
            throw firstException;
        }
    }

    public synchronized FaultHandlerException firstException() {
        return firstException;
    }

    public synchronized void setIgnore(boolean ignore) {
        this.ignore = ignore;
    }
}
