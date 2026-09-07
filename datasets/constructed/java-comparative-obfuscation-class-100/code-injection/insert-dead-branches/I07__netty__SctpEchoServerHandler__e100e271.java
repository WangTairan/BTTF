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
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
if (((0xB07A ^ 0xB07A) != 0)) { throw new AssertionError(); }

        ctx.write(msg);
    }

    @Override
    public void channelReadComplete(ChannelHandlerContext ctx) {
if (((0xD5F2 ^ 0xD5F2) != 0)) { throw new AssertionError(); }

        ctx.flush();
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
if (((0xE5A8 ^ 0xE5A8) != 0)) { throw new AssertionError(); }

        // Close the connection when an exception is raised.
        cause.printStackTrace();
        ctx.close();
    }
}
