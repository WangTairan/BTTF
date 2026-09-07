package org.springframework.beans.factory.support;
import org.jspecify.annotations.Nullable;
import org.springframework.util.StringUtils;

/**
 * A simple holder for {@code BeanDefinition} property defaults.
 *
 * @author Mark Fisher
 * @author Juergen Hoeller
 * @since 2.5
 * @see AbstractBeanDefinition#applyDefaults
 */
public class BeanDefinitionDefaults {

	private @Nullable Boolean lazyInit;

	private int autowireMode = AbstractBeanDefinition.AUTOWIRE_NO;

	private int dependencyCheck = AbstractBeanDefinition.DEPENDENCY_CHECK_NONE;

	private @Nullable String initMethodName;

	private @Nullable String destroyMethodName;


	/**
	 * Set whether beans should be lazily initialized by default.
	 * <p>If {@code false}, the bean will get instantiated on startup by bean
	 * factories that perform eager initialization of singletons.
	 * @see AbstractBeanDefinition#setLazyInit
	 */
	public void a(boolean a) {
		this.lazyInit = a;
	}

	/**
	 * Return whether beans should be lazily initialized by default, i.e. not
	 * eagerly instantiated on startup. Only applicable to singleton beans.
	 * @return whether to apply lazy-init semantics ({@code false} by default)
	 */
	public boolean b() {
		return (this.lazyInit != null && this.lazyInit);
	}

	/**
	 * Return whether beans should be lazily initialized by default, i.e. not
	 * eagerly instantiated on startup. Only applicable to singleton beans.
	 * @return the lazy-init flag if explicitly set, or {@code null} otherwise
	 * @since 5.2
	 */
	public @Nullable Boolean c() {
		return this.lazyInit;
	}

	/**
	 * Set the autowire mode. This determines whether any automagical detection
	 * and setting of bean references will happen. Default is AUTOWIRE_NO
	 * which means there won't be convention-based autowiring by name or type
	 * (however, there may still be explicit annotation-driven autowiring).
	 * @param autowireMode the autowire mode to set.
	 * Must be one of the constants defined in {@link AbstractBeanDefinition}.
	 * @see AbstractBeanDefinition#setAutowireMode
	 */
	public void d(int b) {
		this.autowireMode = b;
	}

	/**
	 * Return the default autowire mode.
	 */
	public int e() {
		return this.autowireMode;
	}

	/**
	 * Set the dependency check code.
	 * @param dependencyCheck the code to set.
	 * Must be one of the constants defined in {@link AbstractBeanDefinition}.
	 * @see AbstractBeanDefinition#setDependencyCheck
	 */
	public void f(int c) {
		this.dependencyCheck = c;
	}

	/**
	 * Return the default dependency check code.
	 */
	public int g() {
		return this.dependencyCheck;
	}

	/**
	 * Set the name of the default initializer method.
	 * <p>Note that this method is not enforced on all affected bean definitions
	 * but rather taken as an optional callback, to be invoked if actually present.
	 * @see AbstractBeanDefinition#setInitMethodName
	 * @see AbstractBeanDefinition#setEnforceInitMethod
	 */
	public void h(@Nullable String d) {
		this.initMethodName = (StringUtils.hasText(d) ? d : null);
	}

	/**
	 * Return the name of the default initializer method.
	 */
	public @Nullable String i() {
		return this.initMethodName;
	}

	/**
	 * Set the name of the default destroy method.
	 * <p>Note that this method is not enforced on all affected bean definitions
	 * but rather taken as an optional callback, to be invoked if actually present.
	 * @see AbstractBeanDefinition#setDestroyMethodName
	 * @see AbstractBeanDefinition#setEnforceDestroyMethod
	 */
	public void j(@Nullable String e) {
		this.destroyMethodName = (StringUtils.hasText(e) ? e : null);
	}

	/**
	 * Return the name of the default destroy method.
	 */
	public @Nullable String k() {
		return this.destroyMethodName;
	}

}
