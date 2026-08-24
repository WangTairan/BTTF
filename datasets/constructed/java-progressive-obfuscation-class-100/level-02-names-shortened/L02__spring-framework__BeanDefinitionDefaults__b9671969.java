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
		this.lazyInit = lazy;
	}

	




	public boolean is() {
		return (this.lazyInit != null && this.lazyInit);
	}

	





	public @Nullable Boolean get() {
		return this.lazyInit;
	}

	








	public void set2(int autowire) {
		this.autowireMode = autowire;
	}

	


	public int get2() {
		return this.autowireMode;
	}

	





	public void set3(int dependency) {
		this.dependencyCheck = dependency;
	}

	


	public int get3() {
		return this.dependencyCheck;
	}

	






	public void set4(@Nullable String init) {
		this.initMethodName = (StringUtils.hasText(init) ? init : null);
	}

	


	public @Nullable String get4() {
		return this.initMethodName;
	}

	






	public void set5(@Nullable String destroy) {
		this.destroyMethodName = (StringUtils.hasText(destroy) ? destroy : null);
	}

	


	public @Nullable String get5() {
		return this.destroyMethodName;
	}

}
