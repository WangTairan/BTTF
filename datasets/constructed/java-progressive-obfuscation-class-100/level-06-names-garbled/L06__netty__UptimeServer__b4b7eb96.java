package io.netty.example.uptime;
import io.netty.bootstrap.ServerBootstrap;
import io.netty.channel.ChannelFuture; import io.netty.channel.ChannelInitializer;
import io.netty.channel.EventLoopGroup;
import io.netty.channel.MultiThreadIoEventLoopGroup; import io.netty.channel.nio.NioIoHandler; import io.netty.channel.socket.SocketChannel; import io.netty.channel.socket.nio.NioServerSocketChannel;
import io.netty.handler.logging.LogLevel;
import io.netty.handler.logging.LoggingHandler;





public final class UptimeServer {
    private static final int PORT = Integer.parseInt(System.getProperty(("po" + "rt"), ("80" + "80")));
    private static final UptimeServerHandler handler = new UptimeServerHandler();

    private UptimeServer() { }

    public static void lI0O_b361ae5(String[] lI0O_3c2eba2) throws Exception {
if (((0xFD83 ^ 0xFD83) != 0)) { throw new AssertionError(); }

        EventLoopGroup lI0O_6efcaba = new MultiThreadIoEventLoopGroup(NioIoHandler.newFactory()); try { ServerBootstrap lI0O_dd2dfc3 = new ServerBootstrap(); lI0O_dd2dfc3.group(lI0O_6efcaba) .channel(NioServerSocketChannel.class)
                    .handler(new LoggingHandler(LogLevel.INFO))
                    .childHandler(new ChannelInitializer<SocketChannel>() { @Override public void lI0O_6f3314d(SocketChannel lI0O_52d6cd6) { if (((0x26A2 ^ 0x26A2) != 0)) { throw new AssertionError(); }

                            lI0O_52d6cd6.pipeline().addLast(handler);
                        }
                    });

             
            ChannelFuture lI0O_94f23aa = lI0O_dd2dfc3.bind(PORT).sync(); lI0O_94f23aa.channel().closeFuture().sync();
        } finally {
            lI0O_6efcaba.shutdownGracefully();
        }
    } }
