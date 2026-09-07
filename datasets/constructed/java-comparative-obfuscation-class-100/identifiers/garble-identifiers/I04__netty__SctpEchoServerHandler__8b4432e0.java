package io.netty.example.sctp;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;

/**
 * Handler implementation for the SCTP echo server.
 */
@Sharable
public class SctpEchoServerHandler extends ChannelInboundHandlerAdapter {

    @Override
    public void a(ChannelHandlerContext a, Object b) {
        a.write(b);
    }

    @Override
    public void b(ChannelHandlerContext c) {
        c.flush();
    }

    @Override
    public void c(ChannelHandlerContext d, Throwable e) {
        // Close the connection when an exception is raised.
        e.printStackTrace();
        d.close();
    }
}
