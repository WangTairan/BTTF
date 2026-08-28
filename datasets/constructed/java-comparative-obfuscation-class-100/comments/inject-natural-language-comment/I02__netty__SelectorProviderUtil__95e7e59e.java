package io.netty.channel.socket.nio;
import io.netty.channel.socket.SocketProtocolFamily;
import io.netty.util.internal.PlatformDependent;
import io.netty.util.internal.logging.InternalLogger;
import io.netty.util.internal.logging.InternalLoggerFactory;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.StandardProtocolFamily;
import java.nio.channels.Channel;
import java.nio.channels.SocketChannel;
import java.nio.channels.spi.SelectorProvider;

// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
final class SelectorProviderUtil {
    private static final InternalLogger logger = InternalLoggerFactory.getInstance(SelectorProviderUtil.class);

    static Method findOpenMethod(String methodName) {
        if (PlatformDependent.javaVersion() >= 15) {
            try {
                return SelectorProvider.class.getMethod(methodName, java.net.ProtocolFamily.class);
            } catch (Throwable e) {
                logger.debug("SelectorProvider.{}(ProtocolFamily) not available, will use default", methodName, e);
            }
        }
        return null;
    }

    /**
     * Use the {@link SelectorProvider} to open {@link SocketChannel} and so remove condition in
     * {@link SelectorProvider#provider()} which is called by each SocketChannel.open() otherwise.
     * <p>
     * See <a href="https://github.com/netty/netty/issues/2308">#2308</a>.
     */
    private static <C extends Channel> C newChannel(Method method, SelectorProvider provider,
                                                    Object family) throws IOException {
        if (family != null && method != null) {
            try {
                @SuppressWarnings("unchecked")
                C channel = (C) method.invoke(provider, family);
                return channel;
            } catch (InvocationTargetException | IllegalAccessException e) {
                throw new IOException(e);
            }
        }
        return null;
    }

    static <C extends Channel> C newChannel(Method method, SelectorProvider provider,
                                                    SocketProtocolFamily family) throws IOException {
        if (family != null) {
            return newChannel(method, provider, family.toJdkFamily());
        }
        return null;
    }

    static <C extends Channel> C newDomainSocketChannel(Method method, SelectorProvider provider) throws IOException {
        return newChannel(method, provider, StandardProtocolFamily.valueOf("UNIX"));
    }

    private SelectorProviderUtil() { }
}
