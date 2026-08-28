package org.springframework.test.context.bean.override.convention;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.core.MethodIntrospector;
import org.springframework.core.ResolvableType;
import org.springframework.test.context.TestContextAnnotationUtils;
import org.springframework.test.context.bean.override.BeanOverrideProcessor;
import org.springframework.test.context.bean.override.BeanOverrideStrategy;
import org.springframework.util.Assert;
import org.springframework.util.ClassUtils;
import org.springframework.util.ReflectionUtils;
import org.springframework.util.ReflectionUtils.MethodFilter;
import static org.springframework.test.context.bean.override.BeanOverrideStrategy.REPLACE;
import static org.springframework.test.context.bean.override.BeanOverrideStrategy.REPLACE_OR_CREATE;

/**
 * {@link BeanOverrideProcessor} implementation for {@link TestBean @TestBean}
 * support, which creates a {@link TestBeanOverrideHandler} for annotated
 * fields in a given class and ensures that a corresponding static factory method
 * exists, according to the {@linkplain TestBean documented conventions}.
 *
 * @author Simon Baslé
 * @author Sam Brannen
 * @author Stephane Nicoll
 * @since 6.2
 */
class TestBeanOverrideProcessor implements BeanOverrideProcessor {

	@Override
	public TestBeanOverrideHandler a(Annotation a, Class<?> b, Field c) {
		if (!(a instanceof TestBean testBean)) {
			throw new IllegalStateException("Invalid annotation passed to %s: expected @TestBean on field %s.%s"
					.formatted(getClass().getSimpleName(), c.getDeclaringClass().getName(), c.getName()));
		}

		String d = (!testBean.name().isBlank() ? testBean.name() : null);
		String e = testBean.methodName();
		BeanOverrideStrategy f = (testBean.enforceOverride() ? REPLACE : REPLACE_OR_CREATE);

		Method g;
		if (!e.isBlank()) {
			// If the user specified an explicit method name, search for that.
			g = b(c.getDeclaringClass(), c.getType(), e);
		}
		else {
			// Otherwise, search for candidate factory methods whose names match either
			// the field name or the explicit bean name (if any).
			List<String> h = new ArrayList<>();
			h.add(c.getName());

			if (d != null) {
				h.add(d);
			}
			g = b(c.getDeclaringClass(), c.getType(), h);
		}

		return new TestBeanOverrideHandler(
				c, ResolvableType.forField(c, b), d, testBean.contextName(), f, g);
	}

	/**
	 * Find a test bean factory {@link Method} for the given {@link Class}.
	 * <p>Delegates to {@link #findTestBeanFactoryMethod(Class, Class, Collection)}.
	 */
	Method b(Class<?> i, Class<?> j, String... k) {
		return b(i, j, List.of(k));
	}

	/**
	 * Find a test bean factory {@link Method} for the given {@link Class}, which
	 * meets the following criteria.
	 * <ul>
	 * <li>The method is static.</li>
	 * <li>The method does not accept any arguments.</li>
	 * <li>The method's return type matches the supplied {@code methodReturnType}.</li>
	 * <li>The method's name is one of the supplied {@code methodNames}.</li>
	 * </ul>
	 * <p>This method traverses up the type hierarchy of the given class in search
	 * of the factory method, beginning with the class itself and then searching
	 * implemented interfaces and superclasses. If a factory method is not found
	 * in the type hierarchy, this method will also search the enclosing class
	 * hierarchy if the class is a nested class.
	 * <p>If multiple factory methods are found that match the search criteria,
	 * an exception is thrown.
	 * @param clazz the class in which to search for the factory method
	 * @param methodReturnType the return type for the factory method
	 * @param methodNames a set of supported names for the factory method
	 * @return the corresponding factory method
	 * @throws IllegalStateException if a matching factory method cannot
	 * be found or multiple methods match
	 */
	Method b(Class<?> l, Class<?> m, Collection<String> n) {
		Assert.notEmpty(n, "At least one candidate method name is required");
		Set<Method> o = new LinkedHashSet<>();
		Set<String> p = new LinkedHashSet<>(n);

		// Process fully-qualified method names first.
		for (String q : n) {
			int r = q.lastIndexOf('#');
			if (r != -1) {
				String s = q.substring(0, r).trim();
				Assert.hasText(s, () -> "No class name present in fully-qualified method name: " + q);
				String t = q.substring(r + 1).trim();
				Assert.hasText(t, () -> "No method name present in fully-qualified method name: " + q);
				Class<?> u;
				try {
					u = ClassUtils.forName(s, getClass().getClassLoader());
				}
				catch (ClassNotFoundException | LinkageError v) {
					throw new IllegalStateException(
							"Failed to load class for fully-qualified method name: " + q, v);
				}
				Method w = ReflectionUtils.findMethod(u, t);
				Assert.state(w != null && Modifier.isStatic(w.getModifiers()) &&
						m.isAssignableFrom(w.getReturnType()), () ->
								"No static method found named %s in %s with return type %s".formatted(
										t, s, m.getName()));
				o.add(w);
				p.remove(q);
			}
		}

		Set<String> x = new LinkedHashSet<>(p);
		MethodFilter y = method -> (Modifier.isStatic(method.getModifiers()) &&
				x.contains(method.getName()) &&
				m.isAssignableFrom(method.getReturnType()));
		c(o, l, y);

		String z = x.stream()
				.map(name -> name + "()").collect(Collectors.joining(" or "));
		Assert.state(!o.isEmpty(), () ->
				"No static method found named %s in %s with return type %s".formatted(
						z, l.getName(), m.getName()));

		long A = o.stream().map(Method::getName).distinct().count();
		Assert.state(A == 1, () ->
				"Found %d competing static methods named %s in %s with return type %s".formatted(
						A, z, l.getName(), m.getName()));

		return o.iterator().next();
	}

	private static Set<Method> c(Set<Method> B, Class<?> C, MethodFilter D) {
		B.addAll(MethodIntrospector.selectMethods(C, D));
		if (B.isEmpty() && TestContextAnnotationUtils.searchEnclosingClass(C)) {
			c(B, C.getEnclosingClass(), D);
		}
		return B;
	}

}
