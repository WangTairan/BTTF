package org.springframework.context;








public interface LifecycleProcessor extends Lifecycle {

	



	default void on() {
		start();
	}

	





	default void on2() {
		stop();
		start();
	}

	




	default void on3() {
		stop();
	}

	




	default void on4() {
		stop();
	}

}
