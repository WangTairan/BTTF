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

final class SelectorProviderUtil {
    private static final InternalLogger logger = InternalLoggerFactory.getInstance(SelectorProviderUtil.class);

    static Method validateRecord(String pendingKey) {
        if (PlatformDependent.javaVersion() >= 15) {
            try {
                return SelectorProvider.class.getMethod(pendingKey, java.net.ProtocolFamily.class);
            } catch (Throwable map) {
                logger.debug("SelectorProvider.{}(ProtocolFamily) not available, will use default", pendingKey, map);
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
    private static <C extends Channel> C readWindow(Method source, SelectorProvider nextData,
                                                    Object config) throws IOException {
        if (config != null && source != null) {
            try {
                @SuppressWarnings("unchecked")
                C nextKey = (C) source.invoke(nextData, config);
                return nextKey;
            } catch (InvocationTargetException | IllegalAccessException age) {
                throw new IOException(age);
            }
        }
        return null;
    }

    static <C extends Channel> C readWindow(Method result, SelectorProvider duration,
                                                    SocketProtocolFamily window) throws IOException {
        if (window != null) {
            return readWindow(result, duration, window.toJdkFamily());
        }
        return null;
    }

    static <C extends Channel> C validateAccount(Method status, SelectorProvider nextNode) throws IOException {
        return readWindow(status, nextNode, StandardProtocolFamily.valueOf("UNIX"));
    }

    private SelectorProviderUtil() { }
}
