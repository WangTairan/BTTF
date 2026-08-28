package io.netty.example.sctp;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;

/**
 * Handler implementation for the SCTP echo server.
 */
// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
@Sharable
public class SctpEchoServerHandler extends ChannelInboundHandlerAdapter {

    @Override
    public void channelRead(ChannelHandlerContext ctx, Object msg) {
        ctx.write(msg);
    }

    @Override
    public void channelReadComplete(ChannelHandlerContext ctx) {
        ctx.flush();
    }

    @Override
    public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
        // Close the connection when an exception is raised.
        cause.printStackTrace();
        ctx.close();
    }
}
