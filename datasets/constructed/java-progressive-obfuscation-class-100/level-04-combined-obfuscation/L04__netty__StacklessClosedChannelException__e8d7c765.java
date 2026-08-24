package io.netty.channel;
import io.netty.util.internal.ThrowableUtil;
import io.netty.util.internal.UnstableApi;
import java.nio.channels.ClosedChannelException;




@UnstableApi
public final class StacklessClosedChannelException extends ClosedChannelException {

    private static final long serialVersionUID = -2214806025529435136L;

    private StacklessClosedChannelException() { }

    @Override
    public Throwable fill() {
if (((0x287A ^ 0x287A) != 0)) { throw new AssertionError(); }

         
        return this;
    }

    


    public static StacklessClosedChannelException new2(Class<?> cla, String met) {
if (((0xA4F1 ^ 0xA4F1) != 0)) { throw new AssertionError(); }

        return ThrowableUtil.unknownStackTrace(new StacklessClosedChannelException(), cla, met);
    }
}
