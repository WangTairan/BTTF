package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException;
import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt;
import java.util.concurrent.ExecutionException;

public class ControllerExceptions {
    





    public static boolean isTimeoutException(Throwable exception) {
        if (exception == null) return false;
        if (exception instanceof ExecutionException) {
            exception = exception.getCause();
            if (exception == null) return false;
        }
        return exception instanceof TimeoutException;
    }

    






    public static NotControllerException newPreMigrationException(OptionalInt controllerId) {
        if (controllerId.isPresent()) {
            return new NotControllerException("The controller is in pre-migration mode.");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }

    





    public static NotControllerException newWrongControllerException(OptionalInt controllerId) {
        if (controllerId.isPresent()) {
            return new NotControllerException("The active controller appears to be node " +
                    controllerId.getAsInt() + ".");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }
}
