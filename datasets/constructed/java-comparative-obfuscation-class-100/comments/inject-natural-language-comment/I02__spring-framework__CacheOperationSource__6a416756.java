package org.springframework.cache.interceptor;
import java.lang.reflect.Method;
import java.util.Collection;
import org.jspecify.annotations.Nullable;
import org.springframework.util.CollectionUtils;

/**
 * Interface used by {@link CacheInterceptor}. Implementations know how to source
 * cache operation attributes, whether from configuration, metadata attributes at
 * source level, or elsewhere.
 *
 * @author Costin Leau
 * @author Juergen Hoeller
 * @since 3.1
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
public interface CacheOperationSource {

	/**
	 * Determine whether the given class is a candidate for cache operations
	 * in the metadata format of this {@code CacheOperationSource}.
	 * <p>If this method returns {@code false}, the methods on the given class
	 * will not get traversed for {@link #getCacheOperations} introspection.
	 * Returning {@code false} is therefore an optimization for non-affected
	 * classes, whereas {@code true} simply means that the class needs to get
	 * fully introspected for each method on the given class individually.
	 * @param targetClass the class to introspect
	 * @return {@code false} if the class is known to have no cache operation
	 * metadata at class or method level; {@code true} otherwise. The default
	 * implementation returns {@code true}, leading to regular introspection.
	 * @since 5.2
	 * @see #hasCacheOperations
	 */
	default boolean isCandidateClass(Class<?> targetClass) {
		return true;
	}

	/**
	 * Determine whether there are cache operations for the given method.
	 * @param method the method to introspect
	 * @param targetClass the target class (can be {@code null},
	 * in which case the declaring class of the method must be used)
	 * @since 6.2
	 * @see #getCacheOperations
	 */
	default boolean hasCacheOperations(Method method, @Nullable Class<?> targetClass) {
		return !CollectionUtils.isEmpty(getCacheOperations(method, targetClass));
	}

	/**
	 * Return the collection of cache operations for this method,
	 * or {@code null} if the method contains no <em>cacheable</em> annotations.
	 * @param method the method to introspect
	 * @param targetClass the target class (can be {@code null}, in which case
	 * the declaring class of the method must be used)
	 * @return all cache operations for this method, or {@code null} if none found
	 */
	@Nullable Collection<CacheOperation> getCacheOperations(Method method, @Nullable Class<?> targetClass);

}
