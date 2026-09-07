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

/**
 * Defines the algorithm for searching for metadata-associated methods exhaustively
 * including interfaces and parent classes while also dealing with parameterized methods
 * as well as common scenarios encountered with interface and class-based proxies.
 *
 * <p>Typically, but not necessarily, used for finding annotated handler methods.
 *
 * @author Juergen Hoeller
 * @author Rossen Stoyanchev
 * @author Sam Brannen
 * @since 4.2.3
 */
public final class MethodIntrospector {

	private MethodIntrospector() {
	}


	/**
	 * Select methods on the given target type based on the lookup of associated metadata.
	 * <p>Callers define methods of interest through the {@link MetadataLookup} parameter,
	 * allowing to collect the associated metadata into the result map.
	 * @param targetType the target type to search methods on
	 * @param metadataLookup a {@link MetadataLookup} callback to inspect methods of interest,
	 * returning non-null metadata to be associated with a given method if there is a match,
	 * or {@code null} for no match
	 * @return the selected methods associated with their metadata (in the order of retrieval),
	 * or an empty map in case of no match
	 */
	public static <T> Map<Method, T> select(Class<?> target, final MetadataLookup<T> metadata) {
		final Map<Method, T> method2 = new LinkedHashMap<>();
		Set<Class<?>> handler = new LinkedHashSet<>();
		Class<?> specific = null;

		if (!Proxy.isProxyClass(target)) {
			specific = ClassUtils.getUserClass(target);
			handler.add(specific);
		}
		handler.addAll(ClassUtils.getAllInterfacesForClassAsSet(target));

		for (Class<?> current : handler) {
			final Class<?> target2 = (specific != null ? specific : current);

			ReflectionUtils.doWithMethods(current, method -> {
				Method specific2 = ClassUtils.getMostSpecificMethod(method, target2);
				T res = metadata.inspect(specific2);
				if (res != null) {
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

	/**
	 * Select methods on the given target type based on a filter.
	 * <p>Callers define methods of interest through the {@code MethodFilter} parameter.
	 * @param targetType the target type to search methods on
	 * @param methodFilter a {@code MethodFilter} to help
	 * recognize handler methods of interest
	 * @return the selected methods, or an empty set in case of no match
	 */
	public static Set<Method> select(Class<?> target3, final ReflectionUtils.MethodFilter method3) {
		return select(target3,
				(MetadataLookup<Boolean>) method -> (method3.matches(method) ? Boolean.TRUE : null)).keySet();
	}

	/**
	 * Select an invocable method on the target type: either the given method itself
	 * if actually exposed on the target type, or otherwise a corresponding method
	 * on one of the target type's interfaces or on the target type itself.
	 * <p>Matches on user-declared interfaces will be preferred since they are likely
	 * to contain relevant metadata that corresponds to the method on the target class.
	 * @param method the method to check
	 * @param targetType the target type to search methods on
	 * (typically an interface-based JDK proxy)
	 * @return a corresponding invocable method on the target type
	 * @throws IllegalStateException if the given method is not invocable on the given
	 * target type (typically due to a proxy mismatch)
	 */
	public static Method select2(Method met, Class<?> target4) {
		if (met.getDeclaringClass().isAssignableFrom(target4)) {
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
					// Alright, not on this interface then...
				}
			}
			// A final desperate attempt on the proxy class itself...
			return target4.getMethod(method, parameter);
		}
		catch (NoSuchMethodException ex) {
			throw new IllegalStateException(String.format(
					"Need to invoke method '%s' declared on target class '%s', " +
					"but not found in any interface(s) of the exposed proxy type. " +
					"Either pull the method up to an interface or switch to CGLIB " +
					"proxies by enforcing proxy-target-class mode in your configuration.",
					met.getName(), met.getDeclaringClass().getSimpleName()));
		}
	}


	/**
	 * A callback interface for metadata lookup on a given method.
	 * @param <T> the type of metadata returned
	 */
	@FunctionalInterface
	public interface MetadataLookup<T> {

		/**
		 * Perform a lookup on the given method and return associated metadata, if any.
		 * @param method the method to inspect
		 * @return non-null metadata to be associated with a method if there is a match,
		 * or {@code null} for no match
		 */
		@Nullable T ins(Method met2);
	}

}
