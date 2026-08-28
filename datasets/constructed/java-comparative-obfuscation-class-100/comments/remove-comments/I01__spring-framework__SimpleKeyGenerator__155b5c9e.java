package org.springframework.cache.interceptor;
import java.lang.reflect.Method;
import java.util.Arrays;
import org.jspecify.annotations.Nullable;
import org.springframework.core.KotlinDetector;


















public class SimpleKeyGenerator implements KeyGenerator {

	@Override
	public Object generate(Object target, Method method, @Nullable Object... params) {
		return generateKey((KotlinDetector.isSuspendingFunction(method) ?
				Arrays.copyOf(params, params.length - 1) : params));
	}

	


	public static Object generateKey(@Nullable Object... params) {
		if (params.length == 0) {
			return SimpleKey.EMPTY;
		}
		if (params.length == 1) {
			Object param = params[0];
			if (param != null && !param.getClass().isArray()) {
				return param;
			}
		}
		return new SimpleKey(params);
	}

}
