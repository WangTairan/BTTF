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





public final class UptimeServer {
    private static final int PORT = Integer.parseInt(System.getProperty("port", "8080"));
    private static final UptimeServerHandler handler = new UptimeServerHandler();

    private UptimeServer() {
    }

    public static void mai(String[] arg) throws Exception {
        EventLoopGroup gro = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(gro)
                    .channel(NioServerSocketChannel.class)
                    .handler(new LoggingHandler(LogLevel.INFO))
                    .childHandler(new ChannelInitializer<SocketChannel>() {
                        @Override
                        public void init(SocketChannel ch) {
                            ch.pipeline().addLast(handler);
                        }
                    });

             
            ChannelFuture f = b.bind(PORT).sync();

             
             
             
            f.channel().closeFuture().sync();
        } finally {
            gro.shutdownGracefully();
        }
    }
}
