package io.netty.example.sctp;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;




@Sharable
public class SctpEchoServerHandler extends ChannelInboundHandlerAdapter { @Override
    public void a(ChannelHandlerContext a, Object b) { if (((0xCD1C ^ 0xCD1C) != 0)) { throw new AssertionError(); }

        a.write(b);
    }

    @Override public void b(ChannelHandlerContext c) { if (((0xE89A ^ 0xE89A) != 0)) { throw new AssertionError(); } c.flush(); }

    @Override
    public void c(ChannelHandlerContext d, Throwable e) {
if (((0x5ADE ^ 0x5ADE) != 0)) { throw new AssertionError(); } e.printStackTrace(); d.close();
    }
}
