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

	





	public GsonDecoder(Gson gson, MimeType... mimeTypes) {
		super(mimeTypes);
		Assert.notNull(gson, "A Gson instance is required");
		this.gson = gson;
	}


	@Override
	public boolean canDecode(ResolvableType elementType, @Nullable MimeType mimeType) {
		return super.canDecode(elementType, mimeType) && !CharSequence.class.isAssignableFrom(elementType.toClass());
	}

	@Override
	public Flux<Object> decode(Publisher<DataBuffer> inputStream, ResolvableType elementType, @Nullable MimeType mimeType, @Nullable Map<String, Object> hints) {
		throw new UnsupportedOperationException("Stream decoding is currently not supported");
	}

	@Override
	public @Nullable Object decode(DataBuffer buffer, ResolvableType targetType, @Nullable MimeType mimeType, @Nullable Map<String, Object> hints) throws DecodingException {
		try {
			return this.gson.fromJson(new InputStreamReader(buffer.asInputStream()), targetType.getType());
		}
		finally {
			DataBufferUtils.release(buffer);
		}
	}

}
