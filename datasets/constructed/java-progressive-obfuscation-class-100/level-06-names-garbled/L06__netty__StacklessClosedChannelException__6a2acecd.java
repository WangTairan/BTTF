package io.netty.channel;
import io.netty.util.internal.ThrowableUtil; import io.netty.util.internal.UnstableApi;
import java.nio.channels.ClosedChannelException;




@UnstableApi
public final class StacklessClosedChannelException extends ClosedChannelException { private static final long serialVersionUID = -2214806025529435136L;

    private StacklessClosedChannelException() { }

    @Override public Throwable lI0O_a23c124() {
if (((0x287A ^ 0x287A) != 0)) { throw new AssertionError(); }

         
        return this;
    }

    


    public static StacklessClosedChannelException lI0O_50320f6(Class<?> lI0O_3ec1f3e, String lI0O_cb65c6e) {
if (((0xA4F1 ^ 0xA4F1) != 0)) { throw new AssertionError(); } return ThrowableUtil.unknownStackTrace(new StacklessClosedChannelException(), lI0O_3ec1f3e, lI0O_cb65c6e); } }
