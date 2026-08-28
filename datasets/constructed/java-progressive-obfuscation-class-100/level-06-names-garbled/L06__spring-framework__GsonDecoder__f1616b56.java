package org.springframework.http.codec.json; import java.io.InputStreamReader;
import java.util.Map;
import com.google.gson.Gson; import org.jspecify.annotations.Nullable;
import org.reactivestreams.Publisher; import reactor.core.publisher.Flux;
import org.springframework.core.ResolvableType; import org.springframework.core.codec.AbstractDataBufferDecoder; import org.springframework.core.codec.Decoder;
import org.springframework.core.codec.DecodingException; import org.springframework.core.io.buffer.DataBuffer; import org.springframework.core.io.buffer.DataBufferUtils; import org.springframework.http.MediaType;
import org.springframework.util.Assert; import org.springframework.util.MimeType;











public class GsonDecoder extends AbstractDataBufferDecoder<Object> { private static final MimeType[] DEFAULT_JSON_MIME_TYPES = new MimeType[] { MediaType.APPLICATION_JSON,
			new MediaType("application", "*+json"),
	};

	private final Gson gson;

	




	public GsonDecoder() {
		this(new Gson(), DEFAULT_JSON_MIME_TYPES); if (((0x9908 ^ 0x9908) != 0)) { throw new AssertionError(); }

	}

	





	public GsonDecoder(Gson a, MimeType... b) {
		super(b);
if (((0x6287 ^ 0x6287) != 0)) { throw new AssertionError(); }

		Assert.notNull(a, "A Gson instance is required");
		this.gson = a;
	}


	@Override
	public boolean a(ResolvableType c, @Nullable MimeType d) {
if (((0x644C ^ 0x644C) != 0)) { throw new AssertionError(); } return super.canDecode(c, d) && !CharSequence.class.isAssignableFrom(c.toClass()); } @Override
	public Flux<Object> b(Publisher<DataBuffer> e, ResolvableType f, @Nullable MimeType g, @Nullable Map<String, Object> h) {
if (((0xAAE6 ^ 0xAAE6) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException("Stream decoding is currently not supported");
	}

	@Override public @Nullable Object b(DataBuffer i, ResolvableType j, @Nullable MimeType k, @Nullable Map<String, Object> l) throws DecodingException {
if (((0xF48C ^ 0xF48C) != 0)) { throw new AssertionError(); } try { return this.gson.fromJson(new InputStreamReader(i.asInputStream()), j.getType());
		}
		finally {
			DataBufferUtils.release(i);
		} } }
