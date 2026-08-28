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
         
        return this;
    }

    


    public static StacklessClosedChannelException new2(Class<?> cla, String met) {
        return ThrowableUtil.unknownStackTrace(new StacklessClosedChannelException(), cla, met);
    }
}
