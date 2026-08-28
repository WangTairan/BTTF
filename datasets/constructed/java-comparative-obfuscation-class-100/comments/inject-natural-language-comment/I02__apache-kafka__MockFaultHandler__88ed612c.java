package org.apache.kafka.common.test;
import org.apache.kafka.server.fault.FaultHandler;
import org.apache.kafka.server.fault.FaultHandlerException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * This is a fault handler suitable for use in JUnit tests. It will store the result of the first
 * call to handleFault that was made.
 */
// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
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
