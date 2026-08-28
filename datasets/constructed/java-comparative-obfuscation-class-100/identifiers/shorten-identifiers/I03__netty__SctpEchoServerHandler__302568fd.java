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
    public void channel(ChannelHandlerContext ctx, Object msg) {
        ctx.write(msg);
    }

    @Override
    public void channel2(ChannelHandlerContext ctx) {
        ctx.flush();
    }

    @Override
    public void exception(ChannelHandlerContext ctx, Throwable cau) {
        // Close the connection when an exception is raised.
        cau.printStackTrace();
        ctx.close();
    }
}
