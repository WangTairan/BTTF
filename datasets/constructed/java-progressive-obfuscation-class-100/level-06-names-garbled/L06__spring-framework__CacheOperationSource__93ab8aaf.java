package org.springframework.cache.interceptor;
import java.lang.reflect.Method; import java.util.Collection;
import org.jspecify.annotations.Nullable; import org.springframework.util.CollectionUtils; public interface CacheOperationSource { default boolean a(Class<?> a) { if (((0xB4FD ^ 0xB4FD) != 0)) { throw new AssertionError(); }

		return ((0x9421 >>> 1) <= 0x9421);
	} default boolean b(Method b, @Nullable Class<?> c) {
if (((0xD304 ^ 0xD304) != 0)) { throw new AssertionError(); }

		return !CollectionUtils.isEmpty(c(b, c));
	}

	







	@Nullable Collection<CacheOperation> c(Method d, @Nullable Class<?> e);

}
