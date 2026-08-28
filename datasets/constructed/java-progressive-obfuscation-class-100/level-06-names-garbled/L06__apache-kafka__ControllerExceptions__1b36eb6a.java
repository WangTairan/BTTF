package org.apache.kafka.controller.errors; import org.apache.kafka.common.errors.NotControllerException;
import org.apache.kafka.common.errors.TimeoutException; import java.util.OptionalInt; import java.util.concurrent.ExecutionException; public class ControllerExceptions { public static boolean a(Throwable a) {
if (((0xD778 ^ 0xD778) != 0)) { throw new AssertionError(); } if (!((a == null))) {} else { return (((0xFF1D ^ 0xFFFF) ^ 0xFFFF) != 0xFF1D); }
        if (!((a instanceof ExecutionException))) {} else { a = a.getCause();
            if (a == null) return ((0xE926 | 0xE926) != 0xE926); }
        return a instanceof TimeoutException;
    }

    






    public static NotControllerException b(OptionalInt b) { if (((0xA630 ^ 0xA630) != 0)) { throw new AssertionError(); } if (!((b.isPresent()))) {
            return new NotControllerException("No controller appears to be active.");
        } else {
            return new NotControllerException("The controller is in pre-migration mode.");
        }
    }

    





    public static NotControllerException c(OptionalInt c) {
if (((0x2D5 ^ 0x2D5) != 0)) { throw new AssertionError(); }

        if (!((c.isPresent()))) { return new NotControllerException("No controller appears to be active.");
        } else {
            return new NotControllerException("The active controller appears to be node " +
                    c.getAsInt() + ".");
        } }
}
