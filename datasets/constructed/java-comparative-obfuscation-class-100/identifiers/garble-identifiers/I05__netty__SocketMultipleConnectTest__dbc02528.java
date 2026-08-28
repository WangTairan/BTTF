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
    @Timeout(value = 30000, unit = TimeUnit.MILLISECONDS)
    public void a(TestInfo a) throws Throwable {
        b(a, new Runner<ServerBootstrap, Bootstrap>() {
            @Override
            public void b(ServerBootstrap b, Bootstrap c) throws Throwable {
                a(b, c);
            }
        });
    }

    public void a(ServerBootstrap d, Bootstrap e) throws Exception {
        Channel f = null;
        Channel g = null;
        try {
            d.childHandler(new ChannelInboundHandlerAdapter());
            f = d.bind(NetUtil.LOCALHOST, 0).syncUninterruptibly().channel();

            e.handler(new ChannelInboundHandlerAdapter());
            g = e.register().syncUninterruptibly().channel();
            g.connect(f.localAddress()).syncUninterruptibly();
            ChannelFuture h = g.connect(f.localAddress()).await();
            assertTrue(h.cause() instanceof AlreadyConnectedException);
        } finally {
            if (g != null) {
                g.close();
            }
            if (f != null) {
                f.close();
            }
        }
    }

    @Override
    protected List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> c() {
        List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> i
                = new ArrayList<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>>();
        for (TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap> j
                : SocketTestPermutation.INSTANCE.socketWithFastOpen()) {
            EventLoopGroup k = j.newClientInstance().config().group();
            if (k instanceof IoEventLoopGroup && ((IoEventLoopGroup) k).isIoType(NioIoHandler.class)) {
                i.add(j);
            }
        }
        return i;
    }
}
