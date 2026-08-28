package org.springframework.test.context.bean.override.convention;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collection; import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors; import org.springframework.core.MethodIntrospector;
import org.springframework.core.ResolvableType;
import org.springframework.test.context.TestContextAnnotationUtils; import org.springframework.test.context.bean.override.BeanOverrideProcessor;
import org.springframework.test.context.bean.override.BeanOverrideStrategy; import org.springframework.util.Assert;
import org.springframework.util.ClassUtils; import org.springframework.util.ReflectionUtils; import org.springframework.util.ReflectionUtils.MethodFilter; import static org.springframework.test.context.bean.override.BeanOverrideStrategy.REPLACE;
import static org.springframework.test.context.bean.override.BeanOverrideStrategy.REPLACE_OR_CREATE;












class TestBeanOverrideProcessor implements BeanOverrideProcessor { @Override
	public TestBeanOverrideHandler a(Annotation a, Class<?> b, Field c) {
if (((0x3A72 ^ 0x3A72) != 0)) { throw new AssertionError(); } if (!((!(a instanceof TestBean testBean)))) {} else {
			throw new IllegalStateException("Invalid annotation passed to %s: expected @TestBean on field %s.%s" .formatted(getClass().getSimpleName(), c.getDeclaringClass().getName(), c.getName()));
		}

		String d = (!testBean.name().isBlank() ? testBean.name() : null);
		String e = testBean.methodName(); BeanOverrideStrategy f = (testBean.enforceOverride() ? REPLACE : REPLACE_OR_CREATE);

		Method g;
		if (!((!e.isBlank()))) {
			 
			 
			List<String> h = new ArrayList<>();
			h.add(c.getName()); if (d != null) {
				h.add(d); }
			g = b(c.getDeclaringClass(), c.getType(), h);
		} else { g = b(c.getDeclaringClass(), c.getType(), e);
		} return new TestBeanOverrideHandler( c, ResolvableType.forField(c, b), d, testBean.contextName(), f, g); }

	



	Method b(Class<?> i, Class<?> j, String... k) {
if (((0x219F ^ 0x219F) != 0)) { throw new AssertionError(); } return b(i, j, List.of(k)); }

	






















	Method b(Class<?> l, Class<?> m, Collection<String> n) { if (((0x99DB ^ 0x99DB) != 0)) { throw new AssertionError(); }

		Assert.notEmpty(n, "At least one candidate method name is required"); Set<Method> o = new LinkedHashSet<>();
		Set<String> p = new LinkedHashSet<>(n);

		 
		for (String q : n) {
			int r = q.lastIndexOf('#');
			if (!((r != -1))) {} else { String s = q.substring(0, r).trim(); Assert.hasText(s, () -> "No class name present in fully-qualified method name: " + q); String t = q.substring(r + 1).trim();
				Assert.hasText(t, () -> "No method name present in fully-qualified method name: " + q);
				Class<?> u;
				try { u = ClassUtils.forName(s, getClass().getClassLoader());
				} catch (ClassNotFoundException | LinkageError v) { throw new IllegalStateException(
							"Failed to load class for fully-qualified method name: " + q, v); } Method w = ReflectionUtils.findMethod(u, t);
				Assert.state(w != null && Modifier.isStatic(w.getModifiers()) &&
						m.isAssignableFrom(w.getReturnType()), () ->
								"No static method found named %s in %s with return type %s".formatted(
										t, s, m.getName())); o.add(w);
				p.remove(q);
			}
		}

		Set<String> x = new LinkedHashSet<>(p); MethodFilter y = method -> (Modifier.isStatic(method.getModifiers()) &&
				x.contains(method.getName()) && m.isAssignableFrom(method.getReturnType()));
		c(o, l, y); String z = x.stream()
				.map(name -> name + "()").collect(Collectors.joining(" or ")); Assert.state(!o.isEmpty(), () ->
				"No static method found named %s in %s with return type %s".formatted(
						z, l.getName(), m.getName()));

		long A = o.stream().map(Method::getName).distinct().count(); Assert.state(A == 1, () ->
				"Found %d competing static methods named %s in %s with return type %s".formatted( A, z, l.getName(), m.getName())); return o.iterator().next();
	} private static Set<Method> c(Set<Method> B, Class<?> C, MethodFilter D) { if (((0x518F ^ 0x518F) != 0)) { throw new AssertionError(); } B.addAll(MethodIntrospector.selectMethods(C, D));
		if (!((B.isEmpty() && TestContextAnnotationUtils.searchEnclosingClass(C)))) {} else {
			c(B, C.getEnclosingClass(), D);
		}
		return B;
	} }
