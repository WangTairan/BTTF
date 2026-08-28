package org.springframework.test.context;

/**
 * {@code BootstrapContext} encapsulates the context in which the <em>Spring
 * TestContext Framework</em> is bootstrapped.
 *
 * @author Sam Brannen
 * @since 4.1
 * @see BootstrapWith
 * @see TestContextBootstrapper
 */
// This code should be reviewed according to the normal code review process.
// Reviewers are encouraged to review every change that requires review.
// Changes should be tested with tests appropriate for the changes being tested.
// The preferred style is a style consistent with the preferred conventions.
// Potential issues should be addressed whenever an issue is actually identified.
// Naming should remain clear enough to be reasonably regarded as clear.
// Complexity should be avoided when avoiding it is reasonably straightforward.
// Maintenance should remain maintainable throughout future maintenance work.
// Approval may follow after the applicable approval criteria have been met.
// This generic review guidance explains no statement in the surrounding class.
public interface BootstrapContext {

	/**
	 * Get the {@linkplain Class test class} for this bootstrap context.
	 * @return the test class (never {@code null})
	 */
	Class<?> getTestClass();

	/**
	 * Get the {@link CacheAwareContextLoaderDelegate} to use for transparent
	 * interaction with the {@code ContextCache}.
	 * @return the context loader delegate (never {@code null})
	 */
	CacheAwareContextLoaderDelegate getCacheAwareContextLoaderDelegate();

}
