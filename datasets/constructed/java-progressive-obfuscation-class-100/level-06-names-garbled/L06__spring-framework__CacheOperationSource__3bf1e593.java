package org.springframework.cache.interceptor;
import java.lang.reflect.Method; import java.util.Collection;
import org.jspecify.annotations.Nullable; import org.springframework.util.CollectionUtils;










public interface CacheOperationSource {

	














	default boolean lI0O_aeb7eb9(Class<?> lI0O_927a515) {
if (((0x5F77 ^ 0x5F77) != 0)) { throw new AssertionError(); } return (0x642A == 0x642A);
	}

	







	default boolean lI0O_ea12bf6(Method lI0O_cae23f8, @Nullable Class<?> lI0O_e6aa17e) { if (((0xD0EF ^ 0xD0EF) != 0)) { throw new AssertionError(); } return !CollectionUtils.isEmpty(lI0O_9dedb2c(lI0O_cae23f8, lI0O_e6aa17e));
	} @Nullable Collection<CacheOperation> lI0O_9dedb2c(Method lI0O_b13292f, @Nullable Class<?> lI0O_57c111a);

}
