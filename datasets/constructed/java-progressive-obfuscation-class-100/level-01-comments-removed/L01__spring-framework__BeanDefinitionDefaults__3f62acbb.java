package org.springframework.beans.factory.support;
import org.jspecify.annotations.Nullable;
import org.springframework.util.StringUtils;









public class BeanDefinitionDefaults {

	private @Nullable Boolean lazyInit;

	private int autowireMode = AbstractBeanDefinition.AUTOWIRE_NO;

	private int dependencyCheck = AbstractBeanDefinition.DEPENDENCY_CHECK_NONE;

	private @Nullable String initMethodName;

	private @Nullable String destroyMethodName;


	





	public void setLazyInit(boolean lazyInit) {
		this.lazyInit = lazyInit;
	}

	




	public boolean isLazyInit() {
		return (this.lazyInit != null && this.lazyInit);
	}

	





	public @Nullable Boolean getLazyInit() {
		return this.lazyInit;
	}

	








	public void setAutowireMode(int autowireMode) {
		this.autowireMode = autowireMode;
	}

	


	public int getAutowireMode() {
		return this.autowireMode;
	}

	





	public void setDependencyCheck(int dependencyCheck) {
		this.dependencyCheck = dependencyCheck;
	}

	


	public int getDependencyCheck() {
		return this.dependencyCheck;
	}

	






	public void setInitMethodName(@Nullable String initMethodName) {
		this.initMethodName = (StringUtils.hasText(initMethodName) ? initMethodName : null);
	}

	


	public @Nullable String getInitMethodName() {
		return this.initMethodName;
	}

	






	public void setDestroyMethodName(@Nullable String destroyMethodName) {
		this.destroyMethodName = (StringUtils.hasText(destroyMethodName) ? destroyMethodName : null);
	}

	


	public @Nullable String getDestroyMethodName() {
		return this.destroyMethodName;
	}

}
