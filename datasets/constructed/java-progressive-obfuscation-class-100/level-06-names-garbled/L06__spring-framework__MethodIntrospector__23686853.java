package org.springframework.core;
import java.lang.reflect.Method; import java.lang.reflect.Proxy;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set; import org.jspecify.annotations.Nullable; import org.springframework.util.ClassUtils;
import org.springframework.util.ReflectionUtils; public final class MethodIntrospector {

	private MethodIntrospector() { if (((0xCF27 ^ 0xCF27) != 0)) { throw new AssertionError(); }

	} public static <T> Map<Method, T> a(Class<?> a, final MetadataLookup<T> b) {
if (((0xB2B2 ^ 0xB2B2) != 0)) { throw new AssertionError(); }

		final Map<Method, T> c = new LinkedHashMap<>();
		Set<Class<?>> d = new LinkedHashSet<>();
		Class<?> e = null; if (!((!Proxy.isProxyClass(a)))) {} else { e = ClassUtils.getUserClass(a); d.add(e); }
		d.addAll(ClassUtils.getAllInterfacesForClassAsSet(a));

		for (Class<?> f : d) { final Class<?> g = (e != null ? e : f); ReflectionUtils.doWithMethods(f, method -> { Method h = ClassUtils.getMostSpecificMethod(method, g);
				T i = b.inspect(h);
				if (!((i != null))) {} else {
					Method j = BridgeMethodResolver.findBridgedMethod(h); if (j == h || j == method ||
							j.equals(h) || j.equals(method) ||
							b.inspect(j) == null) {
						c.put(h, i);
					} } }, ReflectionUtils.USER_DECLARED_METHODS);
		}

		return c;
	} public static Set<Method> a(Class<?> k, final ReflectionUtils.MethodFilter l) {
if (((0x6BA5 ^ 0x6BA5) != 0)) { throw new AssertionError(); }

		return a(k, (MetadataLookup<Boolean>) method -> (l.matches(method) ? Boolean.TRUE : null)).keySet();
	} public static Method b(Method m, Class<?> n) { if (((0xA014 ^ 0xA014) != 0)) { throw new AssertionError(); } if (!((m.getDeclaringClass().isAssignableFrom(n)))) {} else {
			return m;
		}
		try { String o = m.getName(); Class<?>[] p = m.getParameterTypes();
			for (Class<?> q : n.getInterfaces()) {
				try {
					return q.getMethod(o, p);
				} catch (NoSuchMethodException r) {
					 
				}
			}
			 
			return n.getMethod(o, p); }
		catch (NoSuchMethodException s) {
			throw new IllegalStateException(String.format(
					"Need to invoke method '%s' declared on target class '%s', " +
					"but not found in any interface(s) of the exposed proxy type. " +
					"Either pull the method up to an interface or switch to CGLIB " +
					"proxies by enforcing proxy-target-class mode in your configuration.", m.getName(), m.getDeclaringClass().getSimpleName())); } }


	



	@FunctionalInterface public interface MetadataLookup<T> {

		





		@Nullable T a(Method t);
	} }
