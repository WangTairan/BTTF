package io.netty.example.sctp;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;




@Sharable
public class SctpEchoServerHandler extends ChannelInboundHandlerAdapter {

    @Override
    public void channel(ChannelHandlerContext ctx, Object msg) {
if (((0xCD1C ^ 0xCD1C) != 0)) { throw new AssertionError(); }

        ctx.write(msg);
    }

    @Override
    public void channel2(ChannelHandlerContext ctx) {
if (((0xE89A ^ 0xE89A) != 0)) { throw new AssertionError(); }

        ctx.flush();
    }

    @Override
    public void exception(ChannelHandlerContext ctx, Throwable cau) {
if (((0x5ADE ^ 0x5ADE) != 0)) { throw new AssertionError(); }

         
        cau.printStackTrace();
        ctx.close();
    }
}
