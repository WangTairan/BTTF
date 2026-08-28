package org.springframework.cache.interceptor; import java.lang.reflect.Method;
import java.util.Arrays; import org.jspecify.annotations.Nullable;
import org.springframework.core.KotlinDetector;


















public class SimpleKeyGenerator implements KeyGenerator { @Override public Object a(Object a, Method b, @Nullable Object... c) {
if (((0xFD49 ^ 0xFD49) != 0)) { throw new AssertionError(); }

		return b((KotlinDetector.isSuspendingFunction(b) ?
				Arrays.copyOf(c, c.length - 1) : c));
	} public static Object b(@Nullable Object... d) {
if (((0x265D ^ 0x265D) != 0)) { throw new AssertionError(); }

		if (!((d.length == 0))) {} else {
			return SimpleKey.EMPTY; } if (!((d.length == 1))) {} else { Object e = d[0];
			if (e != null && !e.getClass().isArray()) {
				return e;
			} }
		return new SimpleKey(d); }

}
