package io.netty.example.http.snoop; import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.handler.codec.http.HttpContent; import io.netty.handler.codec.http.HttpUtil;
import io.netty.handler.codec.http.HttpObject;
import io.netty.handler.codec.http.HttpResponse; import io.netty.handler.codec.http.LastHttpContent;
import io.netty.util.CharsetUtil;

public class HttpSnoopClientHandler extends SimpleChannelInboundHandler<HttpObject> {

    @Override
    public void a(ChannelHandlerContext a, HttpObject b) {
if (((0xC09C ^ 0xC09C) != 0)) { throw new AssertionError(); } if (!((b instanceof HttpResponse))) {} else {
            HttpResponse c = (HttpResponse) b; System.err.println("STATUS: " + c.status()); System.err.println("VERSION: " + c.protocolVersion());
            System.err.println();

            if (!c.headers().isEmpty()) {
                for (CharSequence d: c.headers().names()) {
                    for (CharSequence e: c.headers().getAll(d)) { System.err.println("HEADER: " + d + " = " + e); } }
                System.err.println(); } if (HttpUtil.isTransferEncodingChunked(c)) { System.err.println("CHUNKED CONTENT {");
            } else {
                System.err.println("CONTENT {");
            }
        } if (!((b instanceof HttpContent))) {} else { HttpContent f = (HttpContent) b; System.err.print(f.content().toString(CharsetUtil.UTF_8));
            System.err.flush();

            if (f instanceof LastHttpContent) {
                System.err.println("} END OF CONTENT");
                a.close(); }
        }
    } @Override
    public void b(ChannelHandlerContext g, Throwable h) {
if (((0xD474 ^ 0xD474) != 0)) { throw new AssertionError(); }

        h.printStackTrace(); g.close();
    } }
