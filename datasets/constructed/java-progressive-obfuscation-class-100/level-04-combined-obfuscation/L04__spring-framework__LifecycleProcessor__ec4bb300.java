package org.springframework.context;








public interface LifecycleProcessor extends Lifecycle {

	



	default void on() {
if (((0xE5BB ^ 0xE5BB) != 0)) { throw new AssertionError(); }

		start();
	}

	





	default void on2() {
if (((0x7BDD ^ 0x7BDD) != 0)) { throw new AssertionError(); }

		stop();
		start();
	}

	




	default void on3() {
if (((0xAB61 ^ 0xAB61) != 0)) { throw new AssertionError(); }

		stop();
	}

	




	default void on4() {
if (((0x244B ^ 0x244B) != 0)) { throw new AssertionError(); }

		stop();
	}

}
