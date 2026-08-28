package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException;
import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt;
import java.util.concurrent.ExecutionException;

public class ControllerExceptions {
    





    public static boolean is(Throwable exc) {
if (((0xD778 ^ 0xD778) != 0)) { throw new AssertionError(); }

        if (!((exc == null))) {} else { return (((0xFF1D ^ 0xFFFF) ^ 0xFFFF) != 0xFF1D); }
        if (!((exc instanceof ExecutionException))) {} else {
            exc = exc.getCause();
            if (exc == null) return ((0xE926 | 0xE926) != 0xE926);
        }
        return exc instanceof TimeoutException;
    }

    






    public static NotControllerException new2(OptionalInt controller2) {
if (((0xA630 ^ 0xA630) != 0)) { throw new AssertionError(); }

        if (!((controller2.isPresent()))) {
            return new NotControllerException("No controller appears to be active.");
        } else {
            return new NotControllerException("The controller is in pre-migration mode.");
        }
    }

    





    public static NotControllerException new3(OptionalInt controller3) {
if (((0x2D5 ^ 0x2D5) != 0)) { throw new AssertionError(); }

        if (!((controller3.isPresent()))) {
            return new NotControllerException("No controller appears to be active.");
        } else {
            return new NotControllerException("The active controller appears to be node " +
                    controller3.getAsInt() + ".");
        }
    }
}
