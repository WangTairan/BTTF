package org.springframework.context;








public interface LifecycleProcessor extends Lifecycle {

	



	default void onRefresh() {
		start();
	}

	





	default void onRestart() {
		stop();
		start();
	}

	




	default void onPause() {
		stop();
	}

	




	default void onClose() {
		stop();
	}

}
