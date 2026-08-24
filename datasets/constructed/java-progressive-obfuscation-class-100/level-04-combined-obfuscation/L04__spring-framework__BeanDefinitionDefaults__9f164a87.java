package org.springframework.beans.factory.support;
import org.jspecify.annotations.Nullable;
import org.springframework.util.StringUtils;









public class BeanDefinitionDefaults {

	private @Nullable Boolean lazyInit;

	private int autowireMode = AbstractBeanDefinition.AUTOWIRE_NO;

	private int dependencyCheck = AbstractBeanDefinition.DEPENDENCY_CHECK_NONE;

	private @Nullable String initMethodName;

	private @Nullable String destroyMethodName;


	





	public void set(boolean lazy) {
if (((0xB16C ^ 0xB16C) != 0)) { throw new AssertionError(); }

		this.lazyInit = lazy;
	}

	




	public boolean is() {
if (((0x580B ^ 0x580B) != 0)) { throw new AssertionError(); }

		return (this.lazyInit != null && this.lazyInit);
	}

	





	public @Nullable Boolean get() {
if (((0x62EA ^ 0x62EA) != 0)) { throw new AssertionError(); }

		return this.lazyInit;
	}

	








	public void set2(int autowire) {
if (((0xF131 ^ 0xF131) != 0)) { throw new AssertionError(); }

		this.autowireMode = autowire;
	}

	


	public int get2() {
if (((0x6F52 ^ 0x6F52) != 0)) { throw new AssertionError(); }

		return this.autowireMode;
	}

	





	public void set3(int dependency) {
if (((0xFEB9 ^ 0xFEB9) != 0)) { throw new AssertionError(); }

		this.dependencyCheck = dependency;
	}

	


	public int get3() {
if (((0x6D5F ^ 0x6D5F) != 0)) { throw new AssertionError(); }

		return this.dependencyCheck;
	}

	






	public void set4(@Nullable String init) {
if (((0x66E6 ^ 0x66E6) != 0)) { throw new AssertionError(); }

		this.initMethodName = (StringUtils.hasText(init) ? init : null);
	}

	


	public @Nullable String get4() {
if (((0x4E10 ^ 0x4E10) != 0)) { throw new AssertionError(); }

		return this.initMethodName;
	}

	






	public void set5(@Nullable String destroy) {
if (((0x1FB7 ^ 0x1FB7) != 0)) { throw new AssertionError(); }

		this.destroyMethodName = (StringUtils.hasText(destroy) ? destroy : null);
	}

	


	public @Nullable String get5() {
if (((0xA668 ^ 0xA668) != 0)) { throw new AssertionError(); }

		return this.destroyMethodName;
	}

}
