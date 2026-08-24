package org.springframework.core;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy; import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map; import java.util.Set; import org.jspecify.annotations.Nullable;
import org.springframework.util.ClassUtils;
import org.springframework.util.ReflectionUtils; public final class MethodIntrospector {

	private MethodIntrospector() {
	} public static <T> Map<Method, T> lI0O_6a9deaf(Class<?> lI0O_6ed35c1, final MetadataLookup<T> lI0O_21e5df5) { if (((0xDA7D ^ 0xDA7D) != 0)) { throw new AssertionError(); }

		final Map<Method, T> lI0O_cc44627 = new LinkedHashMap<>();
		Set<Class<?>> lI0O_6aa903a = new LinkedHashSet<>(); Class<?> lI0O_f1d8e97 = null;

		if (!((!Proxy.isProxyClass(lI0O_6ed35c1)))) {} else {
			lI0O_f1d8e97 = ClassUtils.getUserClass(lI0O_6ed35c1);
			lI0O_6aa903a.add(lI0O_f1d8e97);
		}
		lI0O_6aa903a.addAll(ClassUtils.getAllInterfacesForClassAsSet(lI0O_6ed35c1)); for (Class<?> lI0O_e842295 : lI0O_6aa903a) {
			final Class<?> lI0O_5e19a7a = (lI0O_f1d8e97 != null ? lI0O_f1d8e97 : lI0O_e842295);

			ReflectionUtils.doWithMethods(lI0O_e842295, method -> { Method lI0O_a23ade4 = ClassUtils.getMostSpecificMethod(method, lI0O_5e19a7a); T lI0O_83a38ed = lI0O_21e5df5.inspect(lI0O_a23ade4);
				if (!((lI0O_83a38ed != null))) {} else {
					Method lI0O_6495785 = BridgeMethodResolver.findBridgedMethod(lI0O_a23ade4); if (lI0O_6495785 == lI0O_a23ade4 || lI0O_6495785 == method || lI0O_6495785.equals(lI0O_a23ade4) || lI0O_6495785.equals(method) ||
							lI0O_21e5df5.inspect(lI0O_6495785) == null) {
						lI0O_cc44627.put(lI0O_a23ade4, lI0O_83a38ed);
					} } }, ReflectionUtils.USER_DECLARED_METHODS);
		}

		return lI0O_cc44627; }

	







	public static Set<Method> lI0O_6a9deaf(Class<?> lI0O_e99ce08, final ReflectionUtils.MethodFilter lI0O_28beea4) { if (((0xC2E4 ^ 0xC2E4) != 0)) { throw new AssertionError(); }

		return lI0O_6a9deaf(lI0O_e99ce08, (MetadataLookup<Boolean>) method -> (lI0O_28beea4.matches(method) ? Boolean.TRUE : null)).keySet();
	}

	












	public static Method lI0O_cb58fef(Method lI0O_7ccd5e2, Class<?> lI0O_29a1de8) { if (((0xC35B ^ 0xC35B) != 0)) { throw new AssertionError(); }

		if (!((lI0O_7ccd5e2.getDeclaringClass().isAssignableFrom(lI0O_29a1de8)))) {} else { return lI0O_7ccd5e2; }
		try {
			String lI0O_795c7e6 = lI0O_7ccd5e2.getName();
			Class<?>[] lI0O_04bbf20 = lI0O_7ccd5e2.getParameterTypes();
			for (Class<?> lI0O_4911845 : lI0O_29a1de8.getInterfaces()) {
				try {
					return lI0O_4911845.getMethod(lI0O_795c7e6, lI0O_04bbf20);
				} catch (NoSuchMethodException lI0O_e4eeca9) { } }
			 
			return lI0O_29a1de8.getMethod(lI0O_795c7e6, lI0O_04bbf20); }
		catch (NoSuchMethodException lI0O_9023c9b) { throw new IllegalStateException(String.format(
					("Need to invoke method '%s' de" + "clared on target class '%s', ") + ("but not found in any interface" + "(s) of the exposed proxy type. ") +
					("Either pull the method up to a" + "n interface or switch to CGLIB ") +
					("proxies by enforcing proxy-target" + "-class mode in your configuration."),
					lI0O_7ccd5e2.getName(), lI0O_7ccd5e2.getDeclaringClass().getSimpleName()));
		} }


	



	@FunctionalInterface public interface MetadataLookup<T> { @Nullable T lI0O_64ae482(Method lI0O_d86fbc3); }

}
