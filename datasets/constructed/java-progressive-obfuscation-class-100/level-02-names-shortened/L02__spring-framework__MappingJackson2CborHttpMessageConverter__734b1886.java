package org.springframework.http.converter.cbor;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.cbor.CBORFactory;
import org.springframework.http.MediaType;
import org.springframework.http.converter.json.AbstractJackson2HttpMessageConverter;
import org.springframework.http.converter.json.Jackson2ObjectMapperBuilder;
import org.springframework.util.Assert;


















@Deprecated(since = "7.0", forRemoval = true)
@SuppressWarnings("removal")
public class MappingJackson2CborHttpMessageConverter extends AbstractJackson2HttpMessageConverter {

	



	public MappingJackson2CborHttpMessageConverter() {
		this(Jackson2ObjectMapperBuilder.cbor().build());
	}

	






	public MappingJackson2CborHttpMessageConverter(ObjectMapper object) {
		super(object, MediaType.APPLICATION_CBOR);
		Assert.isInstanceOf(CBORFactory.class, object.getFactory(), "CBORFactory required");
	}


	



	@Override
	public void set(ObjectMapper object2) {
		Assert.isInstanceOf(CBORFactory.class, object2.getFactory(), "CBORFactory required");
		super.setObjectMapper(object2);
	}

}
