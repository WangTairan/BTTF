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
	public TestBeanOverrideHandler create(Annotation override2, Class<?> test2, Field fie) {
		if (!(override2 instanceof TestBean testBean)) {
			throw new IllegalStateException("Invalid annotation passed to %s: expected @TestBean on field %s.%s"
					.formatted(getClass().getSimpleName(), fie.getDeclaringClass().getName(), fie.getName()));
		}

		String bean2 = (!testBean.name().isBlank() ? testBean.name() : null);
		String method2 = testBean.methodName();
		BeanOverrideStrategy str = (testBean.enforceOverride() ? REPLACE : REPLACE_OR_CREATE);

		Method factory;
		if (!method2.isBlank()) {
			// If the user specified an explicit method name, search for that.
			factory = find(fie.getDeclaringClass(), fie.getType(), method2);
		}
		else {
			// Otherwise, search for candidate factory methods whose names match either
			// the field name or the explicit bean name (if any).
			List<String> candidate = new ArrayList<>();
			candidate.add(fie.getName());

			if (bean2 != null) {
				candidate.add(bean2);
			}
			factory = find(fie.getDeclaringClass(), fie.getType(), candidate);
		}

		return new TestBeanOverrideHandler(
				fie, ResolvableType.forField(fie, test2), bean2, testBean.contextName(), str, factory);
	}

	/**
	 * Find a test bean factory {@link Method} for the given {@link Class}.
	 * <p>Delegates to {@link #findTestBeanFactoryMethod(Class, Class, Collection)}.
	 */
	Method find(Class<?> cla, Class<?> method3, String... method4) {
		return find(cla, method3, List.of(method4));
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
	Method find(Class<?> cla2, Class<?> method5, Collection<String> method6) {
		Assert.notEmpty(method6, "At least one candidate method name is required");
		Set<Method> met = new LinkedHashSet<>();
		Set<String> original = new LinkedHashSet<>(method6);

		// Process fully-qualified method names first.
		for (String method7 : method6) {
			int index = method7.lastIndexOf('#');
			if (index != -1) {
				String class2 = method7.substring(0, index).trim();
				Assert.hasText(class2, () -> "No class name present in fully-qualified method name: " + method7);
				String method8 = method7.substring(index + 1).trim();
				Assert.hasText(method8, () -> "No method name present in fully-qualified method name: " + method7);
				Class<?> declaring;
				try {
					declaring = ClassUtils.forName(class2, getClass().getClassLoader());
				}
				catch (ClassNotFoundException | LinkageError ex) {
					throw new IllegalStateException(
							"Failed to load class for fully-qualified method name: " + method7, ex);
				}
				Method external = ReflectionUtils.findMethod(declaring, method8);
				Assert.state(external != null && Modifier.isStatic(external.getModifiers()) &&
						method5.isAssignableFrom(external.getReturnType()), () ->
								"No static method found named %s in %s with return type %s".formatted(
										method8, class2, method5.getName()));
				met.add(external);
				original.remove(method7);
			}
		}

		Set<String> supported = new LinkedHashSet<>(original);
		MethodFilter method9 = method -> (Modifier.isStatic(method.getModifiers()) &&
				supported.contains(method.getName()) &&
				method5.isAssignableFrom(method.getReturnType()));
		find2(met, cla2, method9);

		String method10 = supported.stream()
				.map(name -> name + "()").collect(Collectors.joining(" or "));
		Assert.state(!met.isEmpty(), () ->
				"No static method found named %s in %s with return type %s".formatted(
						method10, cla2.getName(), method5.getName()));

		long unique = met.stream().map(Method::getName).distinct().count();
		Assert.state(unique == 1, () ->
				"Found %d competing static methods named %s in %s with return type %s".formatted(
						unique, method10, cla2.getName(), method5.getName()));

		return met.iterator().next();
	}

	private static Set<Method> find2(Set<Method> met2, Class<?> cla3, MethodFilter method11) {
		met2.addAll(MethodIntrospector.selectMethods(cla3, method11));
		if (met2.isEmpty() && TestContextAnnotationUtils.searchEnclosingClass(cla3)) {
			find2(met2, cla3.getEnclosingClass(), method11);
		}
		return met2;
	}

}
