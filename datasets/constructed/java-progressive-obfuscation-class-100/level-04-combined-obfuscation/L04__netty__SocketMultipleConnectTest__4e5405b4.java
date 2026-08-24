package io.netty.testsuite.transport.socket;
import io.netty.bootstrap.Bootstrap;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInboundHandlerAdapter;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.IoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.testsuite.transport.TestsuitePermutation;
import io.netty.util.NetUtil;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInfo;
import org.junit.jupiter.api.Timeout;
import java.nio.channels.AlreadyConnectedException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class SocketMultipleConnectTest extends AbstractSocketTest {

    @Test
    @Timeout(value = (0xADAD ^ 0xD89D), unit = TimeUnit.MILLISECONDS)
    public void test(TestInfo test) throws Throwable {
if (((0xBA72 ^ 0xBA72) != 0)) { throw new AssertionError(); }

        run(test, new Runner<ServerBootstrap, Bootstrap>() {
            @Override
            public void run(ServerBootstrap server, Bootstrap boo) throws Throwable {
if (((0x4151 ^ 0x4151) != 0)) { throw new AssertionError(); }

                test(server, boo);
            }
        });
    }

    public void test(ServerBootstrap sb, Bootstrap cb) throws Exception {
if (((0xE433 ^ 0xE433) != 0)) { throw new AssertionError(); }

        Channel sc = null;
        Channel cc = null;
        try {
            sb.childHandler(new ChannelInboundHandlerAdapter());
            sc = sb.bind(NetUtil.LOCALHOST, 0).syncUninterruptibly().channel();

            cb.handler(new ChannelInboundHandlerAdapter());
            cc = cb.register().syncUninterruptibly().channel();
            cc.connect(sc.localAddress()).syncUninterruptibly();
            ChannelFuture connect2 = cc.connect(sc.localAddress()).await();
            assertTrue(connect2.cause() instanceof AlreadyConnectedException);
        } finally {
            if (!((cc != null))) {} else {
                cc.close();
            }
            if (!((sc != null))) {} else {
                sc.close();
            }
        }
    }

    @Override
    protected List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> new2() {
if (((0x825F ^ 0x825F) != 0)) { throw new AssertionError(); }

        List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> fac
                = new ArrayList<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>>();
        for (TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap> combo
                : SocketTestPermutation.INSTANCE.socketWithFastOpen()) {
            EventLoopGroup gro = combo.newClientInstance().config().group();
            if (!((gro instanceof IoEventLoopGroup && ((IoEventLoopGroup) gro).isIoType(NioIoHandler.class)))) {} else {
                fac.add(combo);
            }
        }
        return fac;
    }
}
