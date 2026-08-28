package org.springframework.cache.interceptor;
import java.lang.reflect.Method;
import java.util.Collection;
import org.jspecify.annotations.Nullable;
import org.springframework.util.CollectionUtils;










public interface CacheOperationSource {

	














	default boolean isCandidateClass(Class<?> targetClass) {
		return true;
	}

	







	default boolean hasCacheOperations(Method method, @Nullable Class<?> targetClass) {
		return !CollectionUtils.isEmpty(getCacheOperations(method, targetClass));
	}

	







	@Nullable Collection<CacheOperation> getCacheOperations(Method method, @Nullable Class<?> targetClass);

}
