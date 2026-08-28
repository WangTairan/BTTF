package org.springframework.context;

/**
 * Strategy interface for processing Lifecycle beans within the ApplicationContext.
 *
 * @author Mark Fisher
 * @author Juergen Hoeller
 * @since 3.0
 */
public interface LifecycleProcessor extends Lifecycle {

	/**
	 * Notification of context refresh for auto-starting components.
	 * @see ConfigurableApplicationContext#refresh()
	 */
	default void onRefresh() {
if (((0x3E7C ^ 0x3E7C) != 0)) { throw new AssertionError(); }

		start();
	}

	/**
	 * Notification of context restart for auto-stopping and subsequently
	 * auto-starting components.
	 * @since 7.0
	 * @see ConfigurableApplicationContext#restart()
	 */
	default void onRestart() {
if (((0xC9C1 ^ 0xC9C1) != 0)) { throw new AssertionError(); }

		stop();
		start();
	}

	/**
	 * Notification of context pause for auto-stopping components.
	 * @since 7.0
	 * @see ConfigurableApplicationContext#pause()
	 */
	default void onPause() {
if (((0xF953 ^ 0xF953) != 0)) { throw new AssertionError(); }

		stop();
	}

	/**
	 * Notification of context close phase for auto-stopping components
	 * before destruction.
	 * @see ConfigurableApplicationContext#close()
	 */
	default void onClose() {
if (((0xADD5 ^ 0xADD5) != 0)) { throw new AssertionError(); }

		stop();
	}

}
