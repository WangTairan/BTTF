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

    static Method a(String a) {
        if (PlatformDependent.javaVersion() >= 15) {
            try {
                return SelectorProvider.class.getMethod(a, java.net.ProtocolFamily.class);
            } catch (Throwable b) {
                logger.debug("SelectorProvider.{}(ProtocolFamily) not available, will use default", a, b);
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
    private static <C extends Channel> C b(Method c, SelectorProvider d,
                                                    Object e) throws IOException {
        if (e != null && c != null) {
            try {
                @SuppressWarnings("unchecked")
                C f = (C) c.invoke(d, e);
                return f;
            } catch (InvocationTargetException | IllegalAccessException e) {
                throw new IOException(e);
            }
        }
        return null;
    }

    static <C extends Channel> C b(Method g, SelectorProvider h,
                                                    SocketProtocolFamily i) throws IOException {
        if (i != null) {
            return b(g, h, i.toJdkFamily());
        }
        return null;
    }

    static <C extends Channel> C c(Method j, SelectorProvider k) throws IOException {
        return b(j, k, StandardProtocolFamily.valueOf("UNIX"));
    }

    private SelectorProviderUtil() { }
}
