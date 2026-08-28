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




public final class SctpEchoServer {

    static final int PORT = Integer.parseInt(System.getProperty("port", "8007"));

    public static void mai(String[] arg) throws Exception {
         
        EventLoopGroup gro = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory());
        final SctpEchoServerHandler server = new SctpEchoServerHandler();
        try {
            ServerBootstrap b = new ServerBootstrap();
            b.group(gro)
             .channel(NioSctpServerChannel.class)
             .option(ChannelOption.SO_BACKLOG, (~(-100 - 1)))
             .handler(new LoggingHandler(LogLevel.INFO))
             .childHandler(new ChannelInitializer<SctpChannel>() {
                 @Override
                 public void init(SctpChannel ch) throws Exception {
                     ch.pipeline().addLast(
                              
                             server);
                 }
             });

             
            ChannelFuture f = b.bind(PORT).sync();

             
            f.channel().closeFuture().sync();
        } finally {
             
            gro.shutdownGracefully();
        }
    }
}
