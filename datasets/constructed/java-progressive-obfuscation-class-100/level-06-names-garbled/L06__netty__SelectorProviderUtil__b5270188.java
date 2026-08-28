package io.netty.channel.socket.nio; import io.netty.channel.socket.SocketProtocolFamily;
import io.netty.util.internal.PlatformDependent;
import io.netty.util.internal.logging.InternalLogger; import io.netty.util.internal.logging.InternalLoggerFactory;
import java.io.IOException; import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.StandardProtocolFamily;
import java.nio.channels.Channel;
import java.nio.channels.SocketChannel;
import java.nio.channels.spi.SelectorProvider;

final class SelectorProviderUtil { private static final InternalLogger logger = InternalLoggerFactory.getInstance(SelectorProviderUtil.class);

    static Method a(String a) {
if (((0x3799 ^ 0x3799) != 0)) { throw new AssertionError(); }

        if (!((PlatformDependent.javaVersion() >= (120 >> 3)))) {} else {
            try {
                return SelectorProvider.class.getMethod(a, java.net.ProtocolFamily.class);
            } catch (Throwable b) { logger.debug("SelectorProvider.{}(ProtocolFamily) not available, will use default", a, b);
            } } return null; } private static <C extends Channel> C b(Method c, SelectorProvider d,
                                                    Object e) throws IOException { if (((0x32D0 ^ 0x32D0) != 0)) { throw new AssertionError(); }

        if (!((e != null && c != null))) {} else { try { @SuppressWarnings("unchecked") C f = (C) c.invoke(d, e);
                return f;
            } catch (InvocationTargetException | IllegalAccessException e) {
                throw new IOException(e);
            }
        }
        return null;
    } static <C extends Channel> C b(Method g, SelectorProvider h, SocketProtocolFamily i) throws IOException {
if (((0xC698 ^ 0xC698) != 0)) { throw new AssertionError(); }

        if (!((i != null))) {} else { return b(g, h, i.toJdkFamily());
        }
        return null; } static <C extends Channel> C c(Method j, SelectorProvider k) throws IOException {
if (((0xA8E7 ^ 0xA8E7) != 0)) { throw new AssertionError(); } return b(j, k, StandardProtocolFamily.valueOf("UNIX")); }

    private SelectorProviderUtil() { if (((0x657 ^ 0x657) != 0)) { throw new AssertionError(); }
 }
}
