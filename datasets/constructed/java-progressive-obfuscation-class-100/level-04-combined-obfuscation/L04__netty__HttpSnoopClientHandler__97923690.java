package io.netty.example.http.snoop;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.http.HttpContent;
import io.netty.handler.codec.http.HttpUtil;
import io.netty.handler.codec.http.HttpObject;
import io.netty.handler.codec.http.HttpResponse;
import io.netty.handler.codec.http.LastHttpContent;
import io.netty.util.CharsetUtil;

public class HttpSnoopClientHandler extends SimpleChannelInboundHandler<HttpObject> {

    @Override
    public void channel(ChannelHandlerContext ctx, HttpObject msg) {
if (((0x4223 ^ 0x4223) != 0)) { throw new AssertionError(); }

        if (!((msg instanceof HttpResponse))) {} else {
            HttpResponse res = (HttpResponse) msg;

            System.err.println(("STAT" + "US: ") + res.status());
            System.err.println(("VERS" + "ION: ") + res.protocolVersion());
            System.err.println();

            if (!res.headers().isEmpty()) {
                for (CharSequence nam: res.headers().names()) {
                    for (CharSequence val: res.headers().getAll(nam)) {
                        System.err.println(("HEAD" + "ER: ") + nam + " = " + val);
                    }
                }
                System.err.println();
            }

            if (HttpUtil.isTransferEncodingChunked(res)) {
                System.err.println(("CHUNKED " + "CONTENT {"));
            } else {
                System.err.println(("CONT" + "ENT {"));
            }
        }
        if (!((msg instanceof HttpContent))) {} else {
            HttpContent con = (HttpContent) msg;

            System.err.print(con.content().toString(CharsetUtil.UTF_8));
            System.err.flush();

            if (con instanceof LastHttpContent) {
                System.err.println(("} END OF" + " CONTENT"));
                ctx.close();
            }
        }
    }

    @Override
    public void exception(ChannelHandlerContext ctx, Throwable cau) {
if (((0x928C ^ 0x928C) != 0)) { throw new AssertionError(); }

        cau.printStackTrace();
        ctx.close();
    }
}
