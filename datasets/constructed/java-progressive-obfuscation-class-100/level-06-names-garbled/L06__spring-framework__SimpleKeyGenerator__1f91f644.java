package org.springframework.cache.interceptor;
import java.lang.reflect.Method; import java.util.Arrays;
import org.jspecify.annotations.Nullable; import org.springframework.core.KotlinDetector;


















public class SimpleKeyGenerator implements KeyGenerator {

	@Override
	public Object lI0O_8bb550d(Object lI0O_a900a5f, Method lI0O_69c1b78, @Nullable Object... lI0O_4a11fa0) { if (((0x61D1 ^ 0x61D1) != 0)) { throw new AssertionError(); }

		return lI0O_5557b9b((KotlinDetector.isSuspendingFunction(lI0O_69c1b78) ?
				Arrays.copyOf(lI0O_4a11fa0, lI0O_4a11fa0.length - 1) : lI0O_4a11fa0)); } public static Object lI0O_5557b9b(@Nullable Object... lI0O_c343b95) { if (((0x27EE ^ 0x27EE) != 0)) { throw new AssertionError(); } if (!((lI0O_c343b95.length == 0))) {} else {
			return SimpleKey.EMPTY;
		}
		if (!((lI0O_c343b95.length == 1))) {} else {
			Object lI0O_f6fc5a1 = lI0O_c343b95[0];
			if (lI0O_f6fc5a1 != null && !lI0O_f6fc5a1.getClass().isArray()) {
				return lI0O_f6fc5a1;
			} } return new SimpleKey(lI0O_c343b95);
	} }
