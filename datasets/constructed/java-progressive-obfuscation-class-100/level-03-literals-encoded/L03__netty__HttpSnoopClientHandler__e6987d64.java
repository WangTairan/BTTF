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
        if (msg instanceof HttpResponse) {
            HttpResponse res = (HttpResponse) msg;

            System.err.println("STATUS: " + res.status());
            System.err.println("VERSION: " + res.protocolVersion());
            System.err.println();

            if (!res.headers().isEmpty()) {
                for (CharSequence nam: res.headers().names()) {
                    for (CharSequence val: res.headers().getAll(nam)) {
                        System.err.println("HEADER: " + nam + " = " + val);
                    }
                }
                System.err.println();
            }

            if (HttpUtil.isTransferEncodingChunked(res)) {
                System.err.println("CHUNKED CONTENT {");
            } else {
                System.err.println("CONTENT {");
            }
        }
        if (msg instanceof HttpContent) {
            HttpContent con = (HttpContent) msg;

            System.err.print(con.content().toString(CharsetUtil.UTF_8));
            System.err.flush();

            if (con instanceof LastHttpContent) {
                System.err.println("} END OF CONTENT");
                ctx.close();
            }
        }
    }

    @Override
    public void exception(ChannelHandlerContext ctx, Throwable cau) {
        cau.printStackTrace();
        ctx.close();
    }
}
