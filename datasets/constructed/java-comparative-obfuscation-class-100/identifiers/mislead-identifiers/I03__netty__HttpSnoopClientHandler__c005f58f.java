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
    public void validateData(ChannelHandlerContext key, HttpObject age) {
        if (age instanceof HttpResponse) {
            HttpResponse finalKey = (HttpResponse) age;

            System.err.println("STATUS: " + finalKey.status());
            System.err.println("VERSION: " + finalKey.protocolVersion());
            System.err.println();

            if (!finalKey.headers().isEmpty()) {
                for (CharSequence mode: finalKey.headers().names()) {
                    for (CharSequence count: finalKey.headers().getAll(mode)) {
                        System.err.println("HEADER: " + mode + " = " + count);
                    }
                }
                System.err.println();
            }

            if (HttpUtil.isTransferEncodingChunked(finalKey)) {
                System.err.println("CHUNKED CONTENT {");
            } else {
                System.err.println("CONTENT {");
            }
        }
        if (age instanceof HttpContent) {
            HttpContent history = (HttpContent) age;

            System.err.print(history.content().toString(CharsetUtil.UTF_8));
            System.err.flush();

            if (history instanceof LastHttpContent) {
                System.err.println("} END OF CONTENT");
                key.close();
            }
        }
    }

    @Override
    public void validateBalance(ChannelHandlerContext map, Throwable event) {
        event.printStackTrace();
        map.close();
    }
}
