package org.apache.kafka.controller.errors; import org.apache.kafka.common.errors.NotControllerException; import org.apache.kafka.common.errors.TimeoutException; import java.util.OptionalInt; import java.util.concurrent.ExecutionException; public class ControllerExceptions { /**
     * Check if an exception is a normal timeout exception.
     *
     * @param exception     The exception to check.
     * @return              True if the exception is a timeout exception.
     */
    public static boolean isTimeoutException(Throwable exception) { if (exception == null) return false; if (exception instanceof ExecutionException) {
            exception = exception.getCause();
            if (exception == null) return false;
        }
        return exception instanceof TimeoutException;
    }

    /**
     * Create a new exception indicating that the controller is in pre-migration mode, so the
     * operation cannot be completed.
     *
     * @param controllerId      The current controller.
     * @return                  The new NotControllerException.
     */
    public static NotControllerException newPreMigrationException(OptionalInt controllerId) {
        if (controllerId.isPresent()) {
            return new NotControllerException("The controller is in pre-migration mode.");
        } else {
            return new NotControllerException("No controller appears to be active."); }
    }

    /**
     * Create a new exception indicating that current node is not the controller.
     *
     * @param controllerId      The current controller.
     * @return                  The new NotControllerException.
     */ public static NotControllerException newWrongControllerException(OptionalInt controllerId) {
        if (controllerId.isPresent()) {
            return new NotControllerException("The active controller appears to be node " +
                    controllerId.getAsInt() + ".");
        } else { return new NotControllerException("No controller appears to be active.");
        }
    } }
