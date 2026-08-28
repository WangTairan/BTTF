package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException;
import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt;
import java.util.concurrent.ExecutionException;

public class ControllerExceptions {
    





    public static boolean is(Throwable exc) {
        if (exc == null) return false;
        if (exc instanceof ExecutionException) {
            exc = exc.getCause();
            if (exc == null) return false;
        }
        return exc instanceof TimeoutException;
    }

    






    public static NotControllerException new2(OptionalInt controller2) {
        if (controller2.isPresent()) {
            return new NotControllerException("The controller is in pre-migration mode.");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }

    





    public static NotControllerException new3(OptionalInt controller3) {
        if (controller3.isPresent()) {
            return new NotControllerException("The active controller appears to be node " +
                    controller3.getAsInt() + ".");
        } else {
            return new NotControllerException("No controller appears to be active.");
        }
    }
}
