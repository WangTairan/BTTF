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
			 
			factory = find(fie.getDeclaringClass(), fie.getType(), method2);
		}
		else {
			 
			 
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

	



	Method find(Class<?> cla, Class<?> method3, String... method4) {
		return find(cla, method3, List.of(method4));
	}

	






















	Method find(Class<?> cla2, Class<?> method5, Collection<String> method6) {
		Assert.notEmpty(method6, "At least one candidate method name is required");
		Set<Method> met = new LinkedHashSet<>();
		Set<String> original = new LinkedHashSet<>(method6);

		 
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
