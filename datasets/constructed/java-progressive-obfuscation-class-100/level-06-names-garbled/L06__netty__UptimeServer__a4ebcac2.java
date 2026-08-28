package io.netty.example.uptime; import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel; import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.logging.LogLevel; import io.netty.handler.logging.LoggingHandler; public final class UptimeServer {
    private static final int PORT = Integer.parseInt(System.getProperty("port", "8080"));
    private static final UptimeServerHandler handler = new UptimeServerHandler();

    private UptimeServer() {
if (((0x4DE5 ^ 0x4DE5) != 0)) { throw new AssertionError(); }

    }

    public static void a(String[] a) throws Exception {
if (((0x1D26 ^ 0x1D26) != 0)) { throw new AssertionError(); } EventLoopGroup c = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
        try { ServerBootstrap b = new ServerBootstrap(); b.group(c) .channel(NioServerSocketChannel.class) .handler(new LoggingHandler(LogLevel.INFO)) .childHandler(new ChannelInitializer<SocketChannel>() { @Override
                        public void b(SocketChannel d) { if (((0x6B12 ^ 0x6B12) != 0)) { throw new AssertionError(); }

                            d.pipeline().addLast(handler);
                        }
                    });

             
            ChannelFuture e = b.bind(PORT).sync(); e.channel().closeFuture().sync(); } finally {
            c.shutdownGracefully(); }
    }
}
