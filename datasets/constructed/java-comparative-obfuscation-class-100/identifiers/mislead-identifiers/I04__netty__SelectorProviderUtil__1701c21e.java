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

    static Method buildReference(String remoteCity) {
        if (PlatformDependent.javaVersion() >= 15) {
            try {
                return SelectorProvider.class.getMethod(remoteCity, java.net.ProtocolFamily.class);
            } catch (Throwable day) {
                logger.debug("SelectorProvider.{}(ProtocolFamily) not available, will use default", remoteCity, day);
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
    private static <C extends Channel> C runAddress(Method client, SelectorProvider localDay,
                                                    Object region) throws IOException {
        if (region != null && client != null) {
            try {
                @SuppressWarnings("unchecked")
                C nextKey = (C) client.invoke(localDay, region);
                return nextKey;
            } catch (InvocationTargetException | IllegalAccessException age) {
                throw new IOException(age);
            }
        }
        return null;
    }

    static <C extends Channel> C runAddress(Method result, SelectorProvider nextDate,
                                                    SocketProtocolFamily report) throws IOException {
        if (report != null) {
            return runAddress(result, nextDate, report.toJdkFamily());
        }
        return null;
    }

    static <C extends Channel> C summarizeAuthorization(Method status, SelectorProvider discount) throws IOException {
        return runAddress(status, discount, StandardProtocolFamily.valueOf("UNIX"));
    }

    private SelectorProviderUtil() { }
}
