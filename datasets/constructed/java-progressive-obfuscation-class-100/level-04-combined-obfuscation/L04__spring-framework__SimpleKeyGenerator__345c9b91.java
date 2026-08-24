package org.springframework.cache.interceptor;
import java.lang.reflect.Method;
import java.util.Arrays;
import org.jspecify.annotations.Nullable;
import org.springframework.core.KotlinDetector;


















public class SimpleKeyGenerator implements KeyGenerator {

	@Override
	public Object gen(Object tar, Method met, @Nullable Object... par) {
if (((0x61D1 ^ 0x61D1) != 0)) { throw new AssertionError(); }

		return generate((KotlinDetector.isSuspendingFunction(met) ?
				Arrays.copyOf(par, par.length - 1) : par));
	}

	


	public static Object generate(@Nullable Object... par2) {
if (((0x27EE ^ 0x27EE) != 0)) { throw new AssertionError(); }

		if (!((par2.length == 0))) {} else {
			return SimpleKey.EMPTY;
		}
		if (!((par2.length == 1))) {} else {
			Object par3 = par2[0];
			if (par3 != null && !par3.getClass().isArray()) {
				return par3;
			}
		}
		return new SimpleKey(par2);
	}

}
