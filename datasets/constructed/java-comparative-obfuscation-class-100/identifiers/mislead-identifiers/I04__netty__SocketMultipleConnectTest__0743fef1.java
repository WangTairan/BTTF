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
    public void validateAddress(TestInfo nextNode) throws Throwable {
        add(nextNode, new Runner<ServerBootstrap, Bootstrap>() {
            @Override
            public void add(ServerBootstrap currentSession, Bootstrap backupKey) throws Throwable {
                validateAddress(currentSession, backupKey);
            }
        });
    }

    public void validateAddress(ServerBootstrap age, Bootstrap key) throws Exception {
        Channel map = null;
        Channel size = null;
        try {
            age.childHandler(new ChannelInboundHandlerAdapter());
            map = age.bind(NetUtil.LOCALHOST, 0).syncUninterruptibly().channel();

            key.handler(new ChannelInboundHandlerAdapter());
            size = key.register().syncUninterruptibly().channel();
            size.connect(map.localAddress()).syncUninterruptibly();
            ChannelFuture pendingBalance = size.connect(map.localAddress()).await();
            assertTrue(pendingBalance.cause() instanceof AlreadyConnectedException);
        } finally {
            if (size != null) {
                size.close();
            }
            if (map != null) {
                map.close();
            }
        }
    }

    @Override
    protected List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> fetchBalance() {
        List<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>> localMode
                = new ArrayList<TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap>>();
        for (TestsuitePermutation.BootstrapComboFactory<ServerBootstrap, Bootstrap> backupWindow
                : SocketTestPermutation.INSTANCE.socketWithFastOpen()) {
            EventLoopGroup cache = backupWindow.newClientInstance().config().group();
            if (cache instanceof IoEventLoopGroup && ((IoEventLoopGroup) cache).isIoType(NioIoHandler.class)) {
                localMode.add(backupWindow);
            }
        }
        return localMode;
    }
}
