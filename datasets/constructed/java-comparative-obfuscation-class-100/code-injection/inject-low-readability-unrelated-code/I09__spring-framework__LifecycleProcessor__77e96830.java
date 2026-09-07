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
		start();
	}

	/**
	 * Notification of context restart for auto-stopping and subsequently
	 * auto-starting components.
	 * @since 7.0
	 * @see ConfigurableApplicationContext#restart()
	 */
	default void onRestart() {
{int lI0O_8d8f01dc=0x9449,lI0O_7bbd2238=~lI0O_8d8f01dc;lI0O_8d8f01dc=(lI0O_8d8f01dc&lI0O_7bbd2238)|(lI0O_8d8f01dc^lI0O_8d8f01dc);lI0O_7bbd2238^=lI0O_7bbd2238;}

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
