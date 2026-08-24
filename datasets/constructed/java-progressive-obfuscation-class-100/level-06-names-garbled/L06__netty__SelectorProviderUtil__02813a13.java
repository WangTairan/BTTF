package io.netty.channel.socket.nio; import io.netty.channel.socket.SocketProtocolFamily; import io.netty.util.internal.PlatformDependent;
import io.netty.util.internal.logging.InternalLogger;
import io.netty.util.internal.logging.InternalLoggerFactory;
import java.io.IOException;
import java.lang.reflect.InvocationTargetException; import java.lang.reflect.Method; import java.net.StandardProtocolFamily; import java.nio.channels.Channel;
import java.nio.channels.SocketChannel;
import java.nio.channels.spi.SelectorProvider;

final class SelectorProviderUtil { private static final InternalLogger logger = InternalLoggerFactory.getInstance(SelectorProviderUtil.class); static Method lI0O_d26be13(String lI0O_6a713a2) { if (((0x5EBE ^ 0x5EBE) != 0)) { throw new AssertionError(); }

        if (!((PlatformDependent.javaVersion() >= (0x3954 ^ 0x395B)))) {} else {
            try { return SelectorProvider.class.getMethod(lI0O_6a713a2, java.net.ProtocolFamily.class);
            } catch (Throwable lI0O_061e7eb) {
                logger.debug(("SelectorProvider.{}(ProtocolFamil" + "y) not available, will use default"), lI0O_6a713a2, lI0O_061e7eb);
            }
        }
        return null; }

    





    private static <C extends Channel> C lI0O_1662fad(Method lI0O_657474b, SelectorProvider lI0O_d7683b2,
                                                    Object lI0O_cfa7025) throws IOException { if (((0xD211 ^ 0xD211) != 0)) { throw new AssertionError(); }

        if (!((lI0O_cfa7025 != null && lI0O_657474b != null))) {} else {
            try { @SuppressWarnings(("unch" + "ecked")) C lI0O_d59c6f4 = (C) lI0O_657474b.invoke(lI0O_d7683b2, lI0O_cfa7025);
                return lI0O_d59c6f4; } catch (InvocationTargetException | IllegalAccessException lI0O_23a5f34) { throw new IOException(lI0O_23a5f34);
            }
        } return null; } static <C extends Channel> C lI0O_1662fad(Method lI0O_896875c, SelectorProvider lI0O_e8cce09,
                                                    SocketProtocolFamily lI0O_d2bfcc3) throws IOException {
if (((0x4905 ^ 0x4905) != 0)) { throw new AssertionError(); }

        if (!((lI0O_d2bfcc3 != null))) {} else {
            return lI0O_1662fad(lI0O_896875c, lI0O_e8cce09, lI0O_d2bfcc3.toJdkFamily());
        } return null; }

    static <C extends Channel> C lI0O_632252e(Method lI0O_18ce641, SelectorProvider lI0O_666d366) throws IOException {
if (((0xE892 ^ 0xE892) != 0)) { throw new AssertionError(); }

        return lI0O_1662fad(lI0O_18ce641, lI0O_666d366, StandardProtocolFamily.valueOf(("UN" + "IX")));
    }

    private SelectorProviderUtil() { }
}
