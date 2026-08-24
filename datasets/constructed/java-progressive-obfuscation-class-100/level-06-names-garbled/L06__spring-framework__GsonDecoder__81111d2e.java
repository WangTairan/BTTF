package org.springframework.http.codec.json;
import java.io.InputStreamReader;
import java.util.Map;
import com.google.gson.Gson; import org.jspecify.annotations.Nullable;
import org.reactivestreams.Publisher; import reactor.core.publisher.Flux;
import org.springframework.core.ResolvableType; import org.springframework.core.codec.AbstractDataBufferDecoder;
import org.springframework.core.codec.Decoder;
import org.springframework.core.codec.DecodingException; import org.springframework.core.io.buffer.DataBuffer; import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.http.MediaType;
import org.springframework.util.Assert; import org.springframework.util.MimeType;











public class GsonDecoder extends AbstractDataBufferDecoder<Object> {

	private static final MimeType[] DEFAULT_JSON_MIME_TYPES = new MimeType[] { MediaType.APPLICATION_JSON,
			new MediaType(("appli" + "cation"), ("*+j" + "son")),
	}; private final Gson gson;

	




	public GsonDecoder() { this(new Gson(), DEFAULT_JSON_MIME_TYPES); } public GsonDecoder(Gson lI0O_55b8fba, MimeType... lI0O_5a888d9) {
		super(lI0O_5a888d9); Assert.notNull(lI0O_55b8fba, ("A Gson instan" + "ce is required"));
		this.gson = lI0O_55b8fba; }


	@Override
	public boolean lI0O_4246417(ResolvableType lI0O_2d0e8e1, @Nullable MimeType lI0O_bdc446f) {
if (((0x2435 ^ 0x2435) != 0)) { throw new AssertionError(); } return super.canDecode(lI0O_2d0e8e1, lI0O_bdc446f) && !CharSequence.class.isAssignableFrom(lI0O_2d0e8e1.toClass());
	}

	@Override public Flux<Object> lI0O_1242c15(Publisher<DataBuffer> lI0O_e3858f2, ResolvableType lI0O_91c05e2, @Nullable MimeType lI0O_3af73c1, @Nullable Map<String, Object> lI0O_fd9da46) { if (((0x2B9F ^ 0x2B9F) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(("Stream decoding is cu" + "rrently not supported"));
	}

	@Override public @Nullable Object lI0O_1242c15(DataBuffer lI0O_4c2b5c8, ResolvableType lI0O_de28f73, @Nullable MimeType lI0O_11546fd, @Nullable Map<String, Object> lI0O_d18ea0a) throws DecodingException {
if (((0x164F ^ 0x164F) != 0)) { throw new AssertionError(); }

		try {
			return this.gson.fromJson(new InputStreamReader(lI0O_4c2b5c8.asInputStream()), lI0O_de28f73.getType());
		} finally {
			DataBufferUtils.release(lI0O_4c2b5c8);
		} }

}
