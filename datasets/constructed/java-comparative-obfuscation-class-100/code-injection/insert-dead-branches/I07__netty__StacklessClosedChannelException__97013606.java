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

    private StacklessClosedChannelException() {
if (((0x494A ^ 0x494A) != 0)) { throw new AssertionError(); }
 }

    @Override
    public Throwable fillInStackTrace() {
if (((0xCD11 ^ 0xCD11) != 0)) { throw new AssertionError(); }

        // Suppress a warning since this method doesn't need synchronization
        return this;
    }

    /**
     * Creates a new {@link StacklessClosedChannelException} which has the origin of the given {@link Class} and method.
     */
    public static StacklessClosedChannelException newInstance(Class<?> clazz, String method) {
if (((0x6A9E ^ 0x6A9E) != 0)) { throw new AssertionError(); }

        return ThrowableUtil.unknownStackTrace(new StacklessClosedChannelException(), clazz, method);
    }
}
