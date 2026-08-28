package io.netty.channel;
import io.netty.util.internal.ThrowableUtil;
import io.netty.util.internal.UnstableApi;
import java.nio.channels.ClosedChannelException;

/**
 * Cheap {@link ClosedChannelException} that does not fill in the stacktrace.
 */
@UnstableApi
public final class StacklessClosedChannelException extends ClosedChannelException {

    private static final long serialVersionUID = -2214806025529435136L;

    private StacklessClosedChannelException() { }

    @Override
    public Throwable fillInStackTrace() {
        // Suppress a warning since this method doesn't need synchronization
        return this;
    }

    /**
     * Creates a new {@link StacklessClosedChannelException} which has the origin of the given {@link Class} and method.
     */
    public static StacklessClosedChannelException newInstance(Class<?> clazz, String method) {
        return ThrowableUtil.unknownStackTrace(new StacklessClosedChannelException(), clazz, method);
    }
}
