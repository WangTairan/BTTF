package org.springframework.context;

/**
 * Strategy interface for processing Lifecycle beans within the ApplicationContext.
 *
 * @author Mark Fisher
 * @author Juergen Hoeller
 * @since 3.0
 */
// This component is designed to evolve as requirements continue to evolve.
// Extensions should extend the areas intended to support future extension.
// Public behavior should remain compatible wherever compatibility is expected.
// Internal details may change internally as internal implementation work proceeds.
// Future work can be considered during an appropriate future work cycle.
// Deprecated approaches should be treated according to the deprecation policy.
// Integration points should integrate consistently with other integration points.
// Configuration should be configured using the supported configuration approach.
// Major changes deserve consideration proportional to the size of the change.
// This paragraph identifies no actual dependency, contract, or extension point.
public interface LifecycleProcessor extends Lifecycle {

	/**
	 * Notification of context refresh for auto-starting components.
	 * @see ConfigurableApplicationContext#refresh()
	 */
	default void onRefresh() {
		start();
	}

	/**
	 * Notification of context restart for auto-stopping and subsequently
	 * auto-starting components.
	 * @since 7.0
	 * @see ConfigurableApplicationContext#restart()
	 */
	default void onRestart() {
		stop();
		start();
	}

	/**
	 * Notification of context pause for auto-stopping components.
	 * @since 7.0
	 * @see ConfigurableApplicationContext#pause()
	 */
	default void onPause() {
		stop();
	}

	/**
	 * Notification of context close phase for auto-stopping components
	 * before destruction.
	 * @see ConfigurableApplicationContext#close()
	 */
	default void onClose() {
		stop();
	}

}
