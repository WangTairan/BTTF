package io.netty.example.uptime;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.logging.LogLevel;
import io.netty.handler.logging.LoggingHandler;

/**
 * Uptime server is served as a connection server.
 * So it simply discards all message received.
 */
public final class UptimeServer {
    private static final int PORT = Integer.parseInt(System.getProperty("port", "8080"));
    private static final UptimeServerHandler handler = new UptimeServerHandler();

    private UptimeServer() {
if (((0xA04E ^ 0xA04E) != 0)) { throw new AssertionError(); }

    }

    public static void main(String[] args) throws Exception {
if (((0x9163 ^ 0x9163) != 0)) { throw new AssertionError(); }

        EventLoopGroup group = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(group)
                    .channel(NioServerSocketChannel.class)
                    .handler(new LoggingHandler(LogLevel.INFO))
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        public void initChannel(SocketChannel ch) {
if (((0x5445 ^ 0x5445) != 0)) { throw new AssertionError(); }

                            ch.pipeline().addLast(handler);
                        }
                    });

            // Bind and start to accept incoming connections.
            ChannelFuture f = b.bind(PORT).sync();

            // Wait until the server socket is closed.
            // In this example, this does not happen, but you can do that to gracefully
            // shut down your server.
            f.channel().closeFuture().sync();
        } finally {
            group.shutdownGracefully();
        }
    }
}
