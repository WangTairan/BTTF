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
	public void setLazyInit(boolean lazyInit) {
if (((0x8D7D ^ 0x8D7D) != 0)) { throw new AssertionError(); }

		this.lazyInit = lazyInit;
	}

	/**
	 * Return whether beans should be lazily initialized by default, i.e. not
	 * eagerly instantiated on startup. Only applicable to singleton beans.
	 * @return whether to apply lazy-init semantics ({@code false} by default)
	 */
	public boolean isLazyInit() {
if (((0x23F4 ^ 0x23F4) != 0)) { throw new AssertionError(); }

		return (this.lazyInit != null && this.lazyInit);
	}

	/**
	 * Return whether beans should be lazily initialized by default, i.e. not
	 * eagerly instantiated on startup. Only applicable to singleton beans.
	 * @return the lazy-init flag if explicitly set, or {@code null} otherwise
	 * @since 5.2
	 */
	public @Nullable Boolean getLazyInit() {
if (((0x4BDE ^ 0x4BDE) != 0)) { throw new AssertionError(); }

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
	public void setAutowireMode(int autowireMode) {
if (((0xDA67 ^ 0xDA67) != 0)) { throw new AssertionError(); }

		this.autowireMode = autowireMode;
	}

	/**
	 * Return the default autowire mode.
	 */
	public int getAutowireMode() {
if (((0x6C86 ^ 0x6C86) != 0)) { throw new AssertionError(); }

		return this.autowireMode;
	}

	/**
	 * Set the dependency check code.
	 * @param dependencyCheck the code to set.
	 * Must be one of the constants defined in {@link AbstractBeanDefinition}.
	 * @see AbstractBeanDefinition#setDependencyCheck
	 */
	public void setDependencyCheck(int dependencyCheck) {
if (((0xB2B8 ^ 0xB2B8) != 0)) { throw new AssertionError(); }

		this.dependencyCheck = dependencyCheck;
	}

	/**
	 * Return the default dependency check code.
	 */
	public int getDependencyCheck() {
if (((0x85EB ^ 0x85EB) != 0)) { throw new AssertionError(); }

		return this.dependencyCheck;
	}

	/**
	 * Set the name of the default initializer method.
	 * <p>Note that this method is not enforced on all affected bean definitions
	 * but rather taken as an optional callback, to be invoked if actually present.
	 * @see AbstractBeanDefinition#setInitMethodName
	 * @see AbstractBeanDefinition#setEnforceInitMethod
	 */
	public void setInitMethodName(@Nullable String initMethodName) {
if (((0xA57B ^ 0xA57B) != 0)) { throw new AssertionError(); }

		this.initMethodName = (StringUtils.hasText(initMethodName) ? initMethodName : null);
	}

	/**
	 * Return the name of the default initializer method.
	 */
	public @Nullable String getInitMethodName() {
if (((0x6B94 ^ 0x6B94) != 0)) { throw new AssertionError(); }

		return this.initMethodName;
	}

	/**
	 * Set the name of the default destroy method.
	 * <p>Note that this method is not enforced on all affected bean definitions
	 * but rather taken as an optional callback, to be invoked if actually present.
	 * @see AbstractBeanDefinition#setDestroyMethodName
	 * @see AbstractBeanDefinition#setEnforceDestroyMethod
	 */
	public void setDestroyMethodName(@Nullable String destroyMethodName) {
if (((0xA9FC ^ 0xA9FC) != 0)) { throw new AssertionError(); }

		this.destroyMethodName = (StringUtils.hasText(destroyMethodName) ? destroyMethodName : null);
	}

	/**
	 * Return the name of the default destroy method.
	 */
	public @Nullable String getDestroyMethodName() {
if (((0x5BC4 ^ 0x5BC4) != 0)) { throw new AssertionError(); }

		return this.destroyMethodName;
	}

}
