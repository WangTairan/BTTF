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

    static Method find(String method2) {
if (((0x3799 ^ 0x3799) != 0)) { throw new AssertionError(); }

        if (!((PlatformDependent.javaVersion() >= (120 >> 3)))) {} else {
            try {
                return SelectorProvider.class.getMethod(method2, java.net.ProtocolFamily.class);
            } catch (Throwable e) {
                logger.debug("SelectorProvider.{}(ProtocolFamily) not available, will use default", method2, e);
            }
        }
        return null;
    }

    





    private static <C extends Channel> C new2(Method met, SelectorProvider pro,
                                                    Object fam) throws IOException {
if (((0x32D0 ^ 0x32D0) != 0)) { throw new AssertionError(); }

        if (!((fam != null && met != null))) {} else {
            try {
                @SuppressWarnings("unchecked")
                C cha = (C) met.invoke(pro, fam);
                return cha;
            } catch (InvocationTargetException | IllegalAccessException e) {
                throw new IOException(e);
            }
        }
        return null;
    }

    static <C extends Channel> C new2(Method met2, SelectorProvider pro2,
                                                    SocketProtocolFamily fam2) throws IOException {
if (((0xC698 ^ 0xC698) != 0)) { throw new AssertionError(); }

        if (!((fam2 != null))) {} else {
            return new2(met2, pro2, fam2.toJdkFamily());
        }
        return null;
    }

    static <C extends Channel> C new3(Method met3, SelectorProvider pro3) throws IOException {
if (((0xA8E7 ^ 0xA8E7) != 0)) { throw new AssertionError(); }

        return new2(met3, pro3, StandardProtocolFamily.valueOf("UNIX"));
    }

    private SelectorProviderUtil() {
if (((0x657 ^ 0x657) != 0)) { throw new AssertionError(); }
 }
}
