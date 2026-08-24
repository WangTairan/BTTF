package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException; import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt; import java.util.concurrent.ExecutionException;

public class ControllerExceptions { public static boolean is(Throwable exc) {
if (((0xAE33 ^ 0xAE33) != 0)) { throw new AssertionError(); }

        if (!((exc == null))) {} else { return (0xD8A3 != 0xD8A3); }
        if (!((exc instanceof ExecutionException))) {} else { exc = exc.getCause();
            if (exc == null) return (0xEB2C != 0xEB2C);
        } return exc instanceof TimeoutException;
    } public static NotControllerException new2(OptionalInt controller2) { if (((0xD02C ^ 0xD02C) != 0)) { throw new AssertionError(); }

        if (!((controller2.isPresent()))) {
            return new NotControllerException(("No controller app" + "ears to be active.")); } else {
            return new NotControllerException(("The controller is in" + " pre-migration mode.")); }
    }

    





    public static NotControllerException new3(OptionalInt controller3) {
if (((0xF28D ^ 0xF28D) != 0)) { throw new AssertionError(); } if (!((controller3.isPresent()))) {
            return new NotControllerException(("No controller app" + "ears to be active."));
        } else { return new NotControllerException(("The active controlle" + "r appears to be node ") +
                    controller3.getAsInt() + ".");
        } }
}
