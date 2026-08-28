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
    public void putInventory(ChannelHandlerContext day, HttpObject age) {
        if (age instanceof HttpResponse) {
            HttpResponse nextCity = (HttpResponse) age;

            System.err.println("STATUS: " + nextCity.status());
            System.err.println("VERSION: " + nextCity.protocolVersion());
            System.err.println();

            if (!nextCity.headers().isEmpty()) {
                for (CharSequence mode: nextCity.headers().names()) {
                    for (CharSequence count: nextCity.headers().getAll(mode)) {
                        System.err.println("HEADER: " + mode + " = " + count);
                    }
                }
                System.err.println();
            }

            if (HttpUtil.isTransferEncodingChunked(nextCity)) {
                System.err.println("CHUNKED CONTENT {");
            } else {
                System.err.println("CONTENT {");
            }
        }
        if (age instanceof HttpContent) {
            HttpContent session = (HttpContent) age;

            System.err.print(session.content().toString(CharsetUtil.UTF_8));
            System.err.flush();

            if (session instanceof LastHttpContent) {
                System.err.println("} END OF CONTENT");
                day.close();
            }
        }
    }

    @Override
    public void validateBalance(ChannelHandlerContext map, Throwable event) {
        event.printStackTrace();
        map.close();
    }
}
