package org.apache.kafka.controller.errors;
import org.apache.kafka.common.errors.NotControllerException; import org.apache.kafka.common.errors.TimeoutException;
import java.util.OptionalInt; import java.util.concurrent.ExecutionException;

public class ControllerExceptions { public static boolean lI0O_fc09480(Throwable lI0O_9dc9add) {
if (((0xAE33 ^ 0xAE33) != 0)) { throw new AssertionError(); }

        if (!((lI0O_9dc9add == null))) {} else { return (0xD8A3 != 0xD8A3); }
        if (!((lI0O_9dc9add instanceof ExecutionException))) {} else { lI0O_9dc9add = lI0O_9dc9add.getCause();
            if (lI0O_9dc9add == null) return (0xEB2C != 0xEB2C);
        } return lI0O_9dc9add instanceof TimeoutException;
    } public static NotControllerException lI0O_3087a26(OptionalInt lI0O_607ec56) { if (((0xD02C ^ 0xD02C) != 0)) { throw new AssertionError(); }

        if (!((lI0O_607ec56.isPresent()))) {
            return new NotControllerException(("No controller app" + "ears to be active.")); } else {
            return new NotControllerException(("The controller is in" + " pre-migration mode.")); }
    }

    





    public static NotControllerException lI0O_360c086(OptionalInt lI0O_02f3380) {
if (((0xF28D ^ 0xF28D) != 0)) { throw new AssertionError(); } if (!((lI0O_02f3380.isPresent()))) {
            return new NotControllerException(("No controller app" + "ears to be active."));
        } else { return new NotControllerException(("The active controlle" + "r appears to be node ") +
                    lI0O_02f3380.getAsInt() + ".");
        } }
}
