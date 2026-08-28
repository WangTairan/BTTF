package org.springframework.cache.interceptor;
import java.lang.reflect.Method;
import java.util.Collection;
import org.jspecify.annotations.Nullable;
import org.springframework.util.CollectionUtils;










public interface CacheOperationSource {

	














	default boolean is(Class<?> target) {
		return true;
	}

	







	default boolean has(Method met, @Nullable Class<?> target2) {
		return !CollectionUtils.isEmpty(get(met, target2));
	}

	







	@Nullable Collection<CacheOperation> get(Method met2, @Nullable Class<?> target3);

}
