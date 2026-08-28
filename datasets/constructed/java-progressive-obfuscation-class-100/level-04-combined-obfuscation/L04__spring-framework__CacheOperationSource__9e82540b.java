package org.springframework.cache.interceptor;
import java.lang.reflect.Method;
import java.util.Collection;
import org.jspecify.annotations.Nullable;
import org.springframework.util.CollectionUtils;










public interface CacheOperationSource {

	














	default boolean is(Class<?> target) {
if (((0xB4FD ^ 0xB4FD) != 0)) { throw new AssertionError(); }

		return ((0x9421 >>> 1) <= 0x9421);
	}

	







	default boolean has(Method met, @Nullable Class<?> target2) {
if (((0xD304 ^ 0xD304) != 0)) { throw new AssertionError(); }

		return !CollectionUtils.isEmpty(get(met, target2));
	}

	







	@Nullable Collection<CacheOperation> get(Method met2, @Nullable Class<?> target3);

}
