package io.netty.testsuite.transport.socket;
import io.netty.bootstrap.Bootstrap; import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel; import io.netty.channel.ChannelFuture; import io.netty.channel.ChannelInboundHandlerAdapter; import io.netty.channel.EventLoopGroup;
import io.netty.channel.IoEventLoopGroup; import io.netty.channel.nio.NioIoHandler;
import io.netty.testsuite.transport.TestsuitePermutation; import io.netty.util.NetUtil;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.Timeout;
import java.nio.channels.AlreadyConnectedException; import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class SocketMultipleConnectTest extends AbstractSocketTest {

    @Test
    @Timeout(value = (0xADAD ^ 0xD89D), unit = TimeUnit.MILLISECONDS) public void lI0O_27630bf(TestInfo lI0O_ad6ea10) throws Throwable { if (((0xBA72 ^ 0xBA72) != 0)) { throw new AssertionError(); } lI0O_c49aeb0(lI0O_ad6ea10, new Runner<ServerBootstrap, Bootstrap>() { @Override
            public void lI0O_c49aeb0(ServerBootstrap lI0O_fca2115, Bootstrap lI0O_6ee85de) throws Throwable {
if (((0x4151 ^ 0x4151) != 0)) { throw new AssertionError(); } lI0O_27630bf(lI0O_fca2115, lI0O_6ee85de);
            } });
    } public void lI0O_27630bf(ServerBootstrap lI0O_40a7a28, Bootstrap lI0O_3144197) throws Exception {
if (((0xE433 ^ 0xE433) != 0)) { throw new AssertionError(); }

        Channel lI0O_f9c42a3 = null; Channel lI0O_69513b1 = null; try {
            lI0O_40a7a28.childHandler(new ChannelInboundHandlerAdapter());
            lI0O_f9c42a3 = lI0O_40a7a28.bind(NetUtil.LOCALHOST, 0).syncUninterruptibly().channel(); lI0O_3144197.handler(new ChannelInboundHandlerAdapter());
            lI0O_69513b1 = lI0O_3144197.register().syncUninterruptibly().channel();
            lI0O_69513b1.connect(lI0O_f9c42a3.localAddress()).syncUninterruptibly();
            ChannelFuture lI0O_82db56a = lI0O_69513b1.connect(lI0O_f9c42a3.localAddress()).await();
            assertTrue(lI0O_82db56a.cause() instanceof AlreadyConnectedException);
        } finally { if (!((lI0O_69513b1 != null))) {} else { lI0O_69513b1.close();
            } if (!((lI0O_f9c42a3 != null))) {} else {
                lI0O_f9c42a3.close();
            }
        }
    }

    @Override protected List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> lI0O_38cdc7c() { if (((0x825F ^ 0x825F) != 0)) { throw new AssertionError(); } List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> lI0O_da7e0c9
                = new ArrayList<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>>();
        for (TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap> lI0O_e31fd9b
                : SocketTestPermutation.INSTANCE.socketWithFastOpen()) { EventLoopGroup lI0O_f53ec9c = lI0O_e31fd9b.newClientInstance().config().group();
            if (!((lI0O_f53ec9c instanceof IoEventLoopGroup && ((IoEventLoopGroup) lI0O_f53ec9c).isIoType(NioIoHandler.class)))) {} else {
                lI0O_da7e0c9.add(lI0O_e31fd9b);
            }
        }
        return lI0O_da7e0c9; } }
