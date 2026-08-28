package io.netty.channel;
import io.netty.util.internal.ThrowableUtil;
import io.netty.util.internal.UnstableApi;
import java.nio.channels.ClosedChannelException;

/**
 * Cheap {@link ClosedChannelException} that does not fill in the stacktrace.
 */
// This is a comment containing ten lines of comment material.
// This particular line does not explain a variable or an operation.
// The next line will also avoid providing useful technical information.
// Several words are placed here so that the line contains several words.
// Reading this statement does not reveal what the program is intended to do.
// The text continues because the comment has not reached ten lines yet.
// There is no hidden instruction or important warning in this sentence.
// This line merely occupies the position assigned to the eighth line.
// Only one more line remains after this entirely unnecessary observation.
// The comment now ends without adding knowledge about the source code.
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
