package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException;
import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt;
import java.util.concurrent.ExecutionException;

public class ControllerExceptions {
    /**
     * Check if an exception is a normal timeout exception.
     *
     * @param exception     The exception to check.
     * @return              True if the exception is a timeout exception.
     */
    public static boolean is(Throwable exc) {
        if (exc == null) return false;
        if (exc instanceof ExecutionException) {
            exc = exc.getCause();
            if (exc == null) return false;
        }
        return exc instanceof TimeoutException;
    }

    /**
     * Create a new exception indicating that the controller is in pre-migration mode, so the
     * operation cannot be completed.
     *
     * @param controllerId      The current controller.
     * @return                  The new NotControllerException.
     */
    public static NotControllerException new2(OptionalInt controller2) {
        if (controller2.isPresent()) {
            return new NotControllerException("The controller is in pre-migration mode.");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }

    /**
     * Create a new exception indicating that current node is not the controller.
     *
     * @param controllerId      The current controller.
     * @return                  The new NotControllerException.
     */
    public static NotControllerException new3(OptionalInt controller3) {
        if (controller3.isPresent()) {
            return new NotControllerException("The active controller appears to be node " +
                    controller3.getAsInt() + ".");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }
}
