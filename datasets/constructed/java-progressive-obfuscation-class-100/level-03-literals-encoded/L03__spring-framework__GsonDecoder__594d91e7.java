package org.springframework.http.codec.json;
import java.io.InputStreamReader;
import java.util.Map;
import com.google.gson.Gson;
import org.jspecify.annotations.Nullable;
import org.reactivestreams.Publisher;
import reactor.core.publisher.Flux;
import org.springframework.core.ResolvableType;
import org.springframework.core.codec.AbstractDataBufferDecoder;
import org.springframework.core.codec.Decoder;
import org.springframework.core.codec.DecodingException;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.core.io.buffer.DataBufferUtils;
import org.springframework.http.MediaType;
import org.springframework.util.Assert;
import org.springframework.util.MimeType;











public class GsonDecoder extends AbstractDataBufferDecoder<Object> {

	private static final MimeType[] DEFAULT_JSON_MIME_TYPES = new MimeType[] {
			MediaType.APPLICATION_JSON,
			new MediaType("application", "*+json"),
	};

	private final Gson gson;

	




	public GsonDecoder() {
		this(new Gson(), DEFAULT_JSON_MIME_TYPES);
	}

	





	public GsonDecoder(Gson gso, MimeType... mime) {
		super(mime);
		Assert.notNull(gso, "A Gson instance is required");
		this.gson = gso;
	}


	@Override
	public boolean can(ResolvableType element, @Nullable MimeType mime2) {
		return super.canDecode(element, mime2) && !CharSequence.class.isAssignableFrom(element.toClass());
	}

	@Override
	public Flux<Object> dec(Publisher<DataBuffer> input, ResolvableType element2, @Nullable MimeType mime3, @Nullable Map<String, Object> hin) {
		throw new UnsupportedOperationException("Stream decoding is currently not supported");
	}

	@Override
	public @Nullable Object dec(DataBuffer buf, ResolvableType target, @Nullable MimeType mime4, @Nullable Map<String, Object> hin2) throws DecodingException {
		try {
			return this.gson.fromJson(new InputStreamReader(buf.asInputStream()), target.getType());
		}
		finally {
			DataBufferUtils.release(buf);
		}
	}

}
