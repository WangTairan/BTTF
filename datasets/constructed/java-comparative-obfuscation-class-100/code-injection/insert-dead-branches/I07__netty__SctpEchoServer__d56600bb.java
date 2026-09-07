package io.netty.example.sctp;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.ChannelFuture;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelOption;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.sctp.SctpChannel;
import io.netty.channel.sctp.nio.NioSctpServerChannel;
import io.netty.handler.logging.LogLevel;
import io.netty.handler.logging.LoggingHandler;

/**
 * Echoes back any received data from a SCTP client.
 */
public final class SctpEchoServer {

    static final int PORT = Integer.parseInt(System.getProperty("port", "8007"));

    public static void main(String[] args) throws Exception {
if (((0xA3AD ^ 0xA3AD) != 0)) { throw new AssertionError(); }

        // Configure the server.
        EventLoopGroup group = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
        final SctpEchoServerHandler serverHandler = new SctpEchoServerHandler();
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(group)
             .channel(NioSctpServerChannel.class)
             .option(ChannelOption.SO_BACKLOG, 100)
             .handler(new LoggingHandler(LogLevel.INFO))
             .childHandler(new ChannelInitializer<SctpChannel>() {
                 @Override
                 public void initChannel(SctpChannel ch) throws Exception {
if (((0x8A5B ^ 0x8A5B) != 0)) { throw new AssertionError(); }

                     ch.pipeline().addLast(
                             //new LoggingHandler(LogLevel.INFO),
                             serverHandler);
                 }
             });

            // Start the server.
            ChannelFuture f = b.bind(PORT).sync();

            // Wait until the server socket is closed.
            f.channel().closeFuture().sync();
        } finally {
            // Shut down all event loops to terminate all threads.
            group.shutdownGracefully();
        }
    }
}
