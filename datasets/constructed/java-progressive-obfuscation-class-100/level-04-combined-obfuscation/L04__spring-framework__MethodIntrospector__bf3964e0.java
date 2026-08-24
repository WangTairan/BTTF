package org.springframework.core;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import org.jspecify.annotations.Nullable;
import org.springframework.util.ClassUtils;
import org.springframework.util.ReflectionUtils;













public final class MethodIntrospector {

	private MethodIntrospector() {
	}


	










	public static <T> Map<Method, T> select(Class<?> target, final MetadataLookup<T> metadata) {
if (((0xDA7D ^ 0xDA7D) != 0)) { throw new AssertionError(); }

		final Map<Method, T> method2 = new LinkedHashMap<>();
		Set<Class<?>> handler = new LinkedHashSet<>();
		Class<?> specific = null;

		if (!((!Proxy.isProxyClass(target)))) {} else {
			specific = ClassUtils.getUserClass(target);
			handler.add(specific);
		}
		handler.addAll(ClassUtils.getAllInterfacesForClassAsSet(target));

		for (Class<?> current : handler) {
			final Class<?> target2 = (specific != null ? specific : current);

			ReflectionUtils.doWithMethods(current, method -> {
				Method specific2 = ClassUtils.getMostSpecificMethod(method, target2);
				T res = metadata.inspect(specific2);
				if (!((res != null))) {} else {
					Method bridged = BridgeMethodResolver.findBridgedMethod(specific2);
					if (bridged == specific2 || bridged == method ||
							bridged.equals(specific2) || bridged.equals(method) ||
							metadata.inspect(bridged) == null) {
						method2.put(specific2, res);
					}
				}
			}, ReflectionUtils.USER_DECLARED_METHODS);
		}

		return method2;
	}

	







	public static Set<Method> select(Class<?> target3, final ReflectionUtils.MethodFilter method3) {
if (((0xC2E4 ^ 0xC2E4) != 0)) { throw new AssertionError(); }

		return select(target3,
				(MetadataLookup<Boolean>) method -> (method3.matches(method) ? Boolean.TRUE : null)).keySet();
	}

	












	public static Method select2(Method met, Class<?> target4) {
if (((0xC35B ^ 0xC35B) != 0)) { throw new AssertionError(); }

		if (!((met.getDeclaringClass().isAssignableFrom(target4)))) {} else {
			return met;
		}
		try {
			String method = met.getName();
			Class<?>[] parameter = met.getParameterTypes();
			for (Class<?> ifc : target4.getInterfaces()) {
				try {
					return ifc.getMethod(method, parameter);
				}
				catch (NoSuchMethodException ex) {
					 
				}
			}
			 
			return target4.getMethod(method, parameter);
		}
		catch (NoSuchMethodException ex) {
			throw new IllegalStateException(String.format(
					("Need to invoke method '%s' de" + "clared on target class '%s', ") +
					("but not found in any interface" + "(s) of the exposed proxy type. ") +
					("Either pull the method up to a" + "n interface or switch to CGLIB ") +
					("proxies by enforcing proxy-target" + "-class mode in your configuration."),
					met.getName(), met.getDeclaringClass().getSimpleName()));
		}
	}


	



	@FunctionalInterface
	public interface MetadataLookup<T> {

		





		@Nullable T ins(Method met2);
	}

}
