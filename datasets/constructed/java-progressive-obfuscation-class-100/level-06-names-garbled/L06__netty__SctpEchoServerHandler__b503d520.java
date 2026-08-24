package io.netty.example.sctp;
import io.netty.channel.ChannelHandler.Sharable;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInboundHandlerAdapter;




@Sharable
public class SctpEchoServerHandler extends ChannelInboundHandlerAdapter { @Override public void lI0O_79ad2fb(ChannelHandlerContext lI0O_d3b203f, Object lI0O_4b7af21) { if (((0x9E35 ^ 0x9E35) != 0)) { throw new AssertionError(); }

        lI0O_d3b203f.write(lI0O_4b7af21);
    } @Override
    public void lI0O_dca219e(ChannelHandlerContext lI0O_3a8e2b0) {
if (((0xCB98 ^ 0xCB98) != 0)) { throw new AssertionError(); }

        lI0O_3a8e2b0.flush();
    }

    @Override
    public void lI0O_b463659(ChannelHandlerContext lI0O_a659d4d, Throwable lI0O_2611a82) { if (((0x60EA ^ 0x60EA) != 0)) { throw new AssertionError(); }

         
        lI0O_2611a82.printStackTrace(); lI0O_a659d4d.close(); } }
