package org.springframework.test.context;










public interface BootstrapContext {

	



	Class<?> getTestClass();

	




	CacheAwareContextLoaderDelegate getCacheAwareContextLoaderDelegate();

}
