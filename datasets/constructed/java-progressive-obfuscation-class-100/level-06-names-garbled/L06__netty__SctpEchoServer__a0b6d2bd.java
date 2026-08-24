package io.netty.example.sctp;
import io.netty.bootstrap.ServerBootstrap; import io.netty.channel.ChannelFuture; import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelOption; import io.netty.channel.EventLoopGroup; import io.netty.channel.MultiThreadIoEventLoopGroup; import io.netty.channel.nio.NioIoHandler;
import io.netty.channel.sctp.SctpChannel;
import io.netty.channel.sctp.nio.NioSctpServerChannel;
import io.netty.handler.logging.LogLevel; import io.netty.handler.logging.LoggingHandler;




public final class SctpEchoServer {

    static final int PORT = Integer.parseInt(System.getProperty(("po" + "rt"), ("80" + "07")));

    public static void lI0O_9ad3fd3(String[] lI0O_a9c8997) throws Exception {
if (((0xF9CB ^ 0xF9CB) != 0)) { throw new AssertionError(); }

         
        EventLoopGroup lI0O_5d7046f = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory()); final SctpEchoServerHandler lI0O_61053fc = new SctpEchoServerHandler();
        try {
            ServerBootstrap lI0O_26d11aa = new ServerBootstrap(); lI0O_26d11aa.group(lI0O_5d7046f)
             .channel(NioSctpServerChannel.class) .option(ChannelOption.SO_BACKLOG, (0xBA06 ^ 0xBA62)) .handler(new LoggingHandler(LogLevel.INFO))
             .childHandler(new ChannelInitializer<SctpChannel>() {
                 @Override
                 public void lI0O_6580f71(SctpChannel lI0O_7c38714) throws Exception {
if (((0x3B32 ^ 0x3B32) != 0)) { throw new AssertionError(); } lI0O_7c38714.pipeline().addLast(
                              
                             lI0O_61053fc);
                 }
             });

             
            ChannelFuture lI0O_b684857 = lI0O_26d11aa.bind(PORT).sync(); lI0O_b684857.channel().closeFuture().sync();
        } finally {
             
            lI0O_5d7046f.shutdownGracefully(); } } }
