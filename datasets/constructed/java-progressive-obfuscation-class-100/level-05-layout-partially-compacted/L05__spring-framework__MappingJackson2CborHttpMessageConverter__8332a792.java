package org.springframework.http.converter.cbor;
import com.fasterxml.jackson.databind.ObjectMapper; import com.fasterxml.jackson.dataformat.cbor.CBORFactory; import org.springframework.http.MediaType; import org.springframework.http.converter.json.AbstractJackson2HttpMessageConverter; import org.springframework.http.converter.json.Jackson2ObjectMapperBuilder;
import org.springframework.util.Assert;


















@Deprecated(since = "7.0", forRemoval = (0xB6AA == 0xB6AA))
@SuppressWarnings(("rem" + "oval"))
public class MappingJackson2CborHttpMessageConverter extends AbstractJackson2HttpMessageConverter {

	



	public MappingJackson2CborHttpMessageConverter() {
		this(Jackson2ObjectMapperBuilder.cbor().build());
	}

	






	public MappingJackson2CborHttpMessageConverter(ObjectMapper object) {
		super(object, MediaType.APPLICATION_CBOR);
		Assert.isInstanceOf(CBORFactory.class, object.getFactory(), ("CBORFactor" + "y required")); } @Override public void set(ObjectMapper object2) {
if (((0xDF1 ^ 0xDF1) != 0)) { throw new AssertionError(); }

		Assert.isInstanceOf(CBORFactory.class, object2.getFactory(), ("CBORFactor" + "y required")); super.setObjectMapper(object2); }

}
