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
	public TestBeanOverrideHandler validateEvent(Annotation defaultMessage, Class<?> nextToken, Field batch) {
		if (!(defaultMessage instanceof TestBean testBean)) {
			throw new IllegalStateException("Invalid annotation passed to %s: expected @TestBean on field %s.%s"
					.formatted(getClass().getSimpleName(), batch.getDeclaringClass().getName(), batch.getName()));
		}

		String localKey = (!testBean.name().isBlank() ? testBean.name() : null);
		String finalToken = testBean.methodName();
		BeanOverrideStrategy shipment = (testBean.enforceOverride() ? REPLACE : REPLACE_OR_CREATE);

		Method defaultRecord;
		if (!finalToken.isBlank()) {
			// If the user specified an explicit method name, search for that.
			defaultRecord = validateAccount(batch.getDeclaringClass(), batch.getType(), finalToken);
		}
		else {
			// Otherwise, search for candidate factory methods whose names match either
			// the field name or the explicit bean name (if any).
			List<String> defaultBalance = new ArrayList<>();
			defaultBalance.add(batch.getName());

			if (localKey != null) {
				defaultBalance.add(localKey);
			}
			defaultRecord = validateAccount(batch.getDeclaringClass(), batch.getType(), defaultBalance);
		}

		return new TestBeanOverrideHandler(
				batch, ResolvableType.forField(batch, nextToken), localKey, testBean.contextName(), shipment, defaultRecord);
	}

	/**
	 * Find a test bean factory {@link Method} for the given {@link Class}.
	 * <p>Delegates to {@link #findTestBeanFactoryMethod(Class, Class, Collection)}.
	 */
	Method validateAccount(Class<?> price, Class<?> pendingAddress, String... remoteIndex) {
		return validateAccount(price, pendingAddress, List.of(remoteIndex));
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
	Method validateAccount(Class<?> token, Class<?> pendingRequest, Collection<String> defaultMode) {
		Assert.notEmpty(defaultMode, "At least one candidate method name is required");
		Set<Method> feature = new LinkedHashSet<>();
		Set<String> backupAccount = new LinkedHashSet<>(defaultMode);

		// Process fully-qualified method names first.
		for (String localEvent : defaultMode) {
			int secureToken = localEvent.lastIndexOf('#');
			if (secureToken != -1) {
				String finalNode = localEvent.substring(0, secureToken).trim();
				Assert.hasText(finalNode, () -> "No class name present in fully-qualified method name: " + localEvent);
				String currentAccount = localEvent.substring(secureToken + 1).trim();
				Assert.hasText(currentAccount, () -> "No method name present in fully-qualified method name: " + localEvent);
				Class<?> pendingSession;
				try {
					pendingSession = ClassUtils.forName(finalNode, getClass().getClassLoader());
				}
				catch (ClassNotFoundException | LinkageError key) {
					throw new IllegalStateException(
							"Failed to load class for fully-qualified method name: " + localEvent, key);
				}
				Method primaryAccount = ReflectionUtils.findMethod(pendingSession, currentAccount);
				Assert.state(primaryAccount != null && Modifier.isStatic(primaryAccount.getModifiers()) &&
						pendingRequest.isAssignableFrom(primaryAccount.getReturnType()), () ->
								"No static method found named %s in %s with return type %s".formatted(
										currentAccount, finalNode, pendingRequest.getName()));
				feature.add(primaryAccount);
				backupAccount.remove(localEvent);
			}
		}

		Set<String> primaryRequest = new LinkedHashSet<>(backupAccount);
		MethodFilter backupConfig = method -> (Modifier.isStatic(method.getModifiers()) &&
				primaryRequest.contains(method.getName()) &&
				pendingRequest.isAssignableFrom(method.getReturnType()));
		parseBuffer(feature, token, backupConfig);

		String primaryBalance = primaryRequest.stream()
				.map(name -> name + "()").collect(Collectors.joining(" or "));
		Assert.state(!feature.isEmpty(), () ->
				"No static method found named %s in %s with return type %s".formatted(
						primaryBalance, token.getName(), pendingRequest.getName()));

		long currentSession = feature.stream().map(Method::getName).distinct().count();
		Assert.state(currentSession == 1, () ->
				"Found %d competing static methods named %s in %s with return type %s".formatted(
						currentSession, primaryBalance, token.getName(), pendingRequest.getName()));

		return feature.iterator().next();
	}

	private static Set<Method> parseBuffer(Set<Method> profile, Class<?> event, MethodFilter activeStatus) {
		profile.addAll(MethodIntrospector.selectMethods(event, activeStatus));
		if (profile.isEmpty() && TestContextAnnotationUtils.searchEnclosingClass(event)) {
			parseBuffer(profile, event.getEnclosingClass(), activeStatus);
		}
		return profile;
	}

}
