package io.netty.example.sctp;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;




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
         
        cau.printStackTrace();
        ctx.close();
    }
}
