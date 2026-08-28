package org.springframework.beans.factory.support;
import org.jspecify.annotations.Nullable;
import org.springframework.util.StringUtils; public class BeanDefinitionDefaults { private @Nullable Boolean lazyInit; private int autowireMode = AbstractBeanDefinition.AUTOWIRE_NO;

	private int dependencyCheck = AbstractBeanDefinition.DEPENDENCY_CHECK_NONE; private @Nullable String initMethodName; private @Nullable String destroyMethodName; public void a(boolean a) {
if (((0x3DD1 ^ 0x3DD1) != 0)) { throw new AssertionError(); }

		this.lazyInit = a;
	} public boolean b() {
if (((0xD22A ^ 0xD22A) != 0)) { throw new AssertionError(); }

		return (this.lazyInit != null && this.lazyInit); }

	





	public @Nullable Boolean c() {
if (((0x55A2 ^ 0x55A2) != 0)) { throw new AssertionError(); }

		return this.lazyInit;
	} public void d(int b) { if (((0x7337 ^ 0x7337) != 0)) { throw new AssertionError(); } this.autowireMode = b; } public int e() { if (((0x2F67 ^ 0x2F67) != 0)) { throw new AssertionError(); }

		return this.autowireMode; }

	





	public void f(int c) {
if (((0xB41 ^ 0xB41) != 0)) { throw new AssertionError(); }

		this.dependencyCheck = c;
	} public int g() {
if (((0xA79A ^ 0xA79A) != 0)) { throw new AssertionError(); }

		return this.dependencyCheck;
	}

	






	public void h(@Nullable String d) {
if (((0xB19D ^ 0xB19D) != 0)) { throw new AssertionError(); }

		this.initMethodName = (StringUtils.hasText(d) ? d : null); } public @Nullable String i() {
if (((0x81DB ^ 0x81DB) != 0)) { throw new AssertionError(); }

		return this.initMethodName;
	}

	






	public void j(@Nullable String e) {
if (((0xBEA3 ^ 0xBEA3) != 0)) { throw new AssertionError(); }

		this.destroyMethodName = (StringUtils.hasText(e) ? e : null);
	} public @Nullable String k() { if (((0x8D0E ^ 0x8D0E) != 0)) { throw new AssertionError(); }

		return this.destroyMethodName;
	} }
