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
	public TestBeanOverrideHandler syncOperation(Annotation primaryTransaction, Class<?> sharedMap, Field order) {
		if (!(primaryTransaction instanceof TestBean testBean)) {
			throw new IllegalStateException("Invalid annotation passed to %s: expected @TestBean on field %s.%s"
					.formatted(getClass().getSimpleName(), order.getDeclaringClass().getName(), order.getName()));
		}

		String totalMap = (!testBean.name().isBlank() ? testBean.name() : null);
		String totalScore = testBean.methodName();
		BeanOverrideStrategy localKey = (testBean.enforceOverride() ? REPLACE : REPLACE_OR_CREATE);

		Method currentRegion;
		if (!totalScore.isBlank()) {
			// If the user specified an explicit method name, search for that.
			currentRegion = authenticateConfiguration(order.getDeclaringClass(), order.getType(), totalScore);
		}
		else {
			// Otherwise, search for candidate factory methods whose names match either
			// the field name or the explicit bean name (if any).
			List<String> recentAuthentication = new ArrayList<>();
			recentAuthentication.add(order.getName());

			if (totalMap != null) {
				recentAuthentication.add(totalMap);
			}
			currentRegion = authenticateConfiguration(order.getDeclaringClass(), order.getType(), recentAuthentication);
		}

		return new TestBeanOverrideHandler(
				order, ResolvableType.forField(order, sharedMap), totalMap, testBean.contextName(), localKey, currentRegion);
	}

	/**
	 * Find a test bean factory {@link Method} for the given {@link Class}.
	 * <p>Delegates to {@link #findTestBeanFactoryMethod(Class, Class, Collection)}.
	 */
	Method authenticateConfiguration(Class<?> price, Class<?> cachedPermission, String... globalIndex) {
		return authenticateConfiguration(price, cachedPermission, List.of(globalIndex));
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
	Method authenticateConfiguration(Class<?> token, Class<?> internalShipment, Collection<String> currentCity) {
		Assert.notEmpty(currentCity, "At least one candidate method name is required");
		Set<Method> userAge = new LinkedHashSet<>();
		Set<String> configuredKey = new LinkedHashSet<>(currentCity);

		// Process fully-qualified method names first.
		for (String currentAge : currentCity) {
			int defaultDate = currentAge.lastIndexOf('#');
			if (defaultDate != -1) {
				String userValue = currentAge.substring(0, defaultDate).trim();
				Assert.hasText(userValue, () -> "No class name present in fully-qualified method name: " + currentAge);
				String totalRepository = currentAge.substring(defaultDate + 1).trim();
				Assert.hasText(totalRepository, () -> "No method name present in fully-qualified method name: " + currentAge);
				Class<?> globalDiscount;
				try {
					globalDiscount = ClassUtils.forName(userValue, getClass().getClassLoader());
				}
				catch (ClassNotFoundException | LinkageError day) {
					throw new IllegalStateException(
							"Failed to load class for fully-qualified method name: " + currentAge, day);
				}
				Method backupDiscount = ReflectionUtils.findMethod(globalDiscount, totalRepository);
				Assert.state(backupDiscount != null && Modifier.isStatic(backupDiscount.getModifiers()) &&
						internalShipment.isAssignableFrom(backupDiscount.getReturnType()), () ->
								"No static method found named %s in %s with return type %s".formatted(
										totalRepository, userValue, internalShipment.getName()));
				userAge.add(backupDiscount);
				configuredKey.remove(currentAge);
			}
		}

		Set<String> activeShipment = new LinkedHashSet<>(configuredKey);
		MethodFilter availableMap = method -> (Modifier.isStatic(method.getModifiers()) &&
				activeShipment.contains(method.getName()) &&
				internalShipment.isAssignableFrom(method.getReturnType()));
		getShipment(userAge, token, availableMap);

		String externalAuthentication = activeShipment.stream()
				.map(name -> name + "()").collect(Collectors.joining(" or "));
		Assert.state(!userAge.isEmpty(), () ->
				"No static method found named %s in %s with return type %s".formatted(
						externalAuthentication, token.getName(), internalShipment.getName()));

		long operationalRepository = userAge.stream().map(Method::getName).distinct().count();
		Assert.state(operationalRepository == 1, () ->
				"Found %d competing static methods named %s in %s with return type %s".formatted(
						operationalRepository, externalAuthentication, token.getName(), internalShipment.getName()));

		return userAge.iterator().next();
	}

	private static Set<Method> getShipment(Set<Method> nextAge, Class<?> event, MethodFilter activeStatus) {
		nextAge.addAll(MethodIntrospector.selectMethods(event, activeStatus));
		if (nextAge.isEmpty() && TestContextAnnotationUtils.searchEnclosingClass(event)) {
			getShipment(nextAge, event.getEnclosingClass(), activeStatus);
		}
		return nextAge;
	}

}
