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

    public MockFaultHandler(String name) {
        this.name = name;
    }

    @Override
    public synchronized RuntimeException handleFault(String failureMessage, Throwable cause) {
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
        if (firstException != null && !ignore) {
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
