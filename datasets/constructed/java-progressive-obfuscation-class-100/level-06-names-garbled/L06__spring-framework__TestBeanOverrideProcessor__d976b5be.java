package org.springframework.test.context.bean.override.convention;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field; import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection; import java.util.LinkedHashSet; import java.util.List;
import java.util.Set;
import java.util.stream.Collectors; import org.springframework.core.MethodIntrospector;
import org.springframework.core.ResolvableType;
import org.springframework.test.context.TestContextAnnotationUtils;
import org.springframework.test.context.bean.override.BeanOverrideProcessor; import org.springframework.test.context.bean.override.BeanOverrideStrategy;
import org.springframework.util.Assert; import org.springframework.util.ClassUtils;
import org.springframework.util.ReflectionUtils;
import org.springframework.util.ReflectionUtils.MethodFilter; import static org.springframework.test.context.bean.override.BeanOverrideStrategy.REPLACE;
import static org.springframework.test.context.bean.override.BeanOverrideStrategy.REPLACE_OR_CREATE; class TestBeanOverrideProcessor implements BeanOverrideProcessor { @Override public TestBeanOverrideHandler lI0O_0470457(Annotation lI0O_c535b08, Class<?> lI0O_6002eb4, Field lI0O_1b51fa1) {
if (((0xC17C ^ 0xC17C) != 0)) { throw new AssertionError(); } if (!((!(lI0O_c535b08 instanceof TestBean testBean)))) {} else {
			throw new IllegalStateException(("Invalid annotation passed to %s: " + "expected @TestBean on field %s.%s") .formatted(getClass().getSimpleName(), lI0O_1b51fa1.getDeclaringClass().getName(), lI0O_1b51fa1.getName()));
		}

		String lI0O_1bbe29b = (!testBean.name().isBlank() ? testBean.name() : null); String lI0O_07d4612 = testBean.methodName();
		BeanOverrideStrategy lI0O_aed25a6 = (testBean.enforceOverride() ? REPLACE : REPLACE_OR_CREATE);

		Method lI0O_c322150;
		if (!((!lI0O_07d4612.isBlank()))) {
			 
			 
			List<String> lI0O_b68d7f0 = new ArrayList<>();
			lI0O_b68d7f0.add(lI0O_1b51fa1.getName());

			if (lI0O_1bbe29b != null) { lI0O_b68d7f0.add(lI0O_1bbe29b); }
			lI0O_c322150 = lI0O_c90b5b0(lI0O_1b51fa1.getDeclaringClass(), lI0O_1b51fa1.getType(), lI0O_b68d7f0); } else {
			 
			lI0O_c322150 = lI0O_c90b5b0(lI0O_1b51fa1.getDeclaringClass(), lI0O_1b51fa1.getType(), lI0O_07d4612);
		} return new TestBeanOverrideHandler( lI0O_1b51fa1, ResolvableType.forField(lI0O_1b51fa1, lI0O_6002eb4), lI0O_1bbe29b, testBean.contextName(), lI0O_aed25a6, lI0O_c322150);
	}

	



	Method lI0O_c90b5b0(Class<?> lI0O_80c8b55, Class<?> lI0O_dba79df, String... lI0O_69fc9db) { if (((0x9A37 ^ 0x9A37) != 0)) { throw new AssertionError(); } return lI0O_c90b5b0(lI0O_80c8b55, lI0O_dba79df, List.of(lI0O_69fc9db)); }

	






















	Method lI0O_c90b5b0(Class<?> lI0O_c7551ac, Class<?> lI0O_2bef185, Collection<String> lI0O_010d012) { if (((0x5D ^ 0x5D) != 0)) { throw new AssertionError(); }

		Assert.notEmpty(lI0O_010d012, ("At least one candidate " + "method name is required")); Set<Method> lI0O_875aef4 = new LinkedHashSet<>(); Set<String> lI0O_9022eca = new LinkedHashSet<>(lI0O_010d012);

		 
		for (String lI0O_a26e5ad : lI0O_010d012) {
			int lI0O_1c3d0d1 = lI0O_a26e5ad.lastIndexOf('#'); if (!((lI0O_1c3d0d1 != -1))) {} else { String lI0O_544536d = lI0O_a26e5ad.substring(0, lI0O_1c3d0d1).trim();
				Assert.hasText(lI0O_544536d, () -> ("No class name present in fu" + "lly-qualified method name: ") + lI0O_a26e5ad);
				String lI0O_241a2bc = lI0O_a26e5ad.substring(lI0O_1c3d0d1 + 1).trim();
				Assert.hasText(lI0O_241a2bc, () -> ("No method name present in f" + "ully-qualified method name: ") + lI0O_a26e5ad); Class<?> lI0O_c04728e; try {
					lI0O_c04728e = ClassUtils.forName(lI0O_544536d, getClass().getClassLoader());
				} catch (ClassNotFoundException | LinkageError lI0O_3f1e914) { throw new IllegalStateException(
							("Failed to load class for fu" + "lly-qualified method name: ") + lI0O_a26e5ad, lI0O_3f1e914);
				}
				Method lI0O_60cdc97 = ReflectionUtils.findMethod(lI0O_c04728e, lI0O_241a2bc);
				Assert.state(lI0O_60cdc97 != null && Modifier.isStatic(lI0O_60cdc97.getModifiers()) &&
						lI0O_2bef185.isAssignableFrom(lI0O_60cdc97.getReturnType()), () -> ("No static method found named" + " %s in %s with return type %s").formatted(
										lI0O_241a2bc, lI0O_544536d, lI0O_2bef185.getName()));
				lI0O_875aef4.add(lI0O_60cdc97);
				lI0O_9022eca.remove(lI0O_a26e5ad);
			}
		}

		Set<String> lI0O_c3d7459 = new LinkedHashSet<>(lI0O_9022eca);
		MethodFilter lI0O_5b50b66 = method -> (Modifier.isStatic(method.getModifiers()) && lI0O_c3d7459.contains(method.getName()) && lI0O_2bef185.isAssignableFrom(method.getReturnType()));
		lI0O_5aaf226(lI0O_875aef4, lI0O_c7551ac, lI0O_5b50b66); String lI0O_602424b = lI0O_c3d7459.stream()
				.map(name -> name + "()").collect(Collectors.joining((" o" + "r "))); Assert.state(!lI0O_875aef4.isEmpty(), () -> ("No static method found named" + " %s in %s with return type %s").formatted(
						lI0O_602424b, lI0O_c7551ac.getName(), lI0O_2bef185.getName())); long lI0O_68b2e97 = lI0O_875aef4.stream().map(Method::getName).distinct().count(); Assert.state(lI0O_68b2e97 == 1, () ->
				("Found %d competing static methods " + "named %s in %s with return type %s").formatted(
						lI0O_68b2e97, lI0O_602424b, lI0O_c7551ac.getName(), lI0O_2bef185.getName()));

		return lI0O_875aef4.iterator().next();
	} private static Set<Method> lI0O_5aaf226(Set<Method> lI0O_e78122a, Class<?> lI0O_cf7180e, MethodFilter lI0O_2499150) {
if (((0xF452 ^ 0xF452) != 0)) { throw new AssertionError(); }

		lI0O_e78122a.addAll(MethodIntrospector.selectMethods(lI0O_cf7180e, lI0O_2499150));
		if (!((lI0O_e78122a.isEmpty() && TestContextAnnotationUtils.searchEnclosingClass(lI0O_cf7180e)))) {} else { lI0O_5aaf226(lI0O_e78122a, lI0O_cf7180e.getEnclosingClass(), lI0O_2499150);
		}
		return lI0O_e78122a; }

}
