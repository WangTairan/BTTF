package org.springframework.context;








public interface LifecycleProcessor extends Lifecycle {

	



	default void on() {
if (((0x70C1 ^ 0x70C1) != 0)) { throw new AssertionError(); }

		start();
	}

	





	default void on2() {
if (((0xA690 ^ 0xA690) != 0)) { throw new AssertionError(); }

		stop();
		start();
	}

	




	default void on3() {
if (((0xFF90 ^ 0xFF90) != 0)) { throw new AssertionError(); }

		stop();
	}

	




	default void on4() {
if (((0xBD4E ^ 0xBD4E) != 0)) { throw new AssertionError(); }

		stop();
	}

}
