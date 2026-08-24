package io.netty.example.http.snoop;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler; import io.netty.handler.codec.http.HttpContent;
import io.netty.handler.codec.http.HttpUtil;
import io.netty.handler.codec.http.HttpObject;
import io.netty.handler.codec.http.HttpResponse; import io.netty.handler.codec.http.LastHttpContent;
import io.netty.util.CharsetUtil; public class HttpSnoopClientHandler extends SimpleChannelInboundHandler<HttpObject> {

    @Override
    public void lI0O_8cd9513(ChannelHandlerContext lI0O_cf01037, HttpObject lI0O_a54adda) {
if (((0x4223 ^ 0x4223) != 0)) { throw new AssertionError(); }

        if (!((lI0O_a54adda instanceof HttpResponse))) {} else { HttpResponse lI0O_e1cab1e = (HttpResponse) lI0O_a54adda;

            System.err.println(("STAT" + "US: ") + lI0O_e1cab1e.status());
            System.err.println(("VERS" + "ION: ") + lI0O_e1cab1e.protocolVersion()); System.err.println();

            if (!lI0O_e1cab1e.headers().isEmpty()) {
                for (CharSequence lI0O_b74ed25: lI0O_e1cab1e.headers().names()) { for (CharSequence lI0O_c25841a: lI0O_e1cab1e.headers().getAll(lI0O_b74ed25)) {
                        System.err.println(("HEAD" + "ER: ") + lI0O_b74ed25 + " = " + lI0O_c25841a); }
                }
                System.err.println();
            }

            if (HttpUtil.isTransferEncodingChunked(lI0O_e1cab1e)) {
                System.err.println(("CHUNKED " + "CONTENT {"));
            } else { System.err.println(("CONT" + "ENT {")); } } if (!((lI0O_a54adda instanceof HttpContent))) {} else { HttpContent lI0O_59d7cc4 = (HttpContent) lI0O_a54adda;

            System.err.print(lI0O_59d7cc4.content().toString(CharsetUtil.UTF_8)); System.err.flush(); if (lI0O_59d7cc4 instanceof LastHttpContent) { System.err.println(("} END OF" + " CONTENT")); lI0O_cf01037.close(); }
        }
    } @Override
    public void lI0O_9dfe137(ChannelHandlerContext lI0O_bbd8a72, Throwable lI0O_fee2500) {
if (((0x928C ^ 0x928C) != 0)) { throw new AssertionError(); }

        lI0O_fee2500.printStackTrace(); lI0O_bbd8a72.close();
    }
}
