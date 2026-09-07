package io.netty.testsuite.transport.socket;
import io.netty.bootstrap.Bootstrap; import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInboundHandlerAdapter; import io.netty.channel.EventLoopGroup;
import io.netty.channel.IoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.testsuite.transport.TestsuitePermutation;
import io.netty.util.NetUtil; import org.junit.jupiter.api.Test; import org.junit.jupiter.api.TestInfo; import org.junit.jupiter.api.Timeout; import java.nio.channels.AlreadyConnectedException; import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class SocketMultipleConnectTest extends AbstractSocketTest {

    @Test @Timeout(value = 30000, unit = TimeUnit.MILLISECONDS) public void testMultipleConnect(TestInfo testInfo) throws Throwable {
        run(testInfo, new Runner<ServerBootstrap, Bootstrap>() { @Override
            public void run(ServerBootstrap serverBootstrap, Bootstrap bootstrap) throws Throwable { testMultipleConnect(serverBootstrap, bootstrap);
            }
        }); } public void testMultipleConnect(ServerBootstrap sb, Bootstrap cb) throws Exception {
        Channel sc = null;
        Channel cc = null; try {
            sb.childHandler(new ChannelInboundHandlerAdapter()); sc = sb.bind(NetUtil.LOCALHOST, 0).syncUninterruptibly().channel();

            cb.handler(new ChannelInboundHandlerAdapter());
            cc = cb.register().syncUninterruptibly().channel();
            cc.connect(sc.localAddress()).syncUninterruptibly();
            ChannelFuture connectFuture2 = cc.connect(sc.localAddress()).await();
            assertTrue(connectFuture2.cause() instanceof AlreadyConnectedException); } finally {
            if (cc != null) {
                cc.close();
            }
            if (sc != null) {
                sc.close(); }
        }
    }

    @Override
    protected List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> newFactories() { List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> factories = new ArrayList<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>>();
        for (TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap> comboFactory : SocketTestPermutation.INSTANCE.socketWithFastOpen()) { EventLoopGroup group = comboFactory.newClientInstance().config().group();
            if (group instanceof IoEventLoopGroup && ((IoEventLoopGroup) group).isIoType(NioIoHandler.class)) {
                factories.add(comboFactory); } } return factories; }
}
