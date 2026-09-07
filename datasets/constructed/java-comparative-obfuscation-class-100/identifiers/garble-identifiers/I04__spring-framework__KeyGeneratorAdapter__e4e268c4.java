package org.springframework.cache.jcache.interceptor;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import javax.cache.annotation.CacheInvocationParameter;
import javax.cache.annotation.CacheKeyGenerator;
import javax.cache.annotation.CacheKeyInvocationContext;
import org.jspecify.annotations.Nullable;
import org.springframework.cache.interceptor.KeyGenerator;
import org.springframework.util.Assert;
import org.springframework.util.CollectionUtils;

/**
 * Spring's {@link KeyGenerator} implementation that either delegates to a standard JSR-107
 * {@link javax.cache.annotation.CacheKeyGenerator}, or wrap a standard {@link KeyGenerator}
 * so that only relevant parameters are handled.
 *
 * @author Stephane Nicoll
 * @author Juergen Hoeller
 * @since 4.1
 */
class KeyGeneratorAdapter implements KeyGenerator {

	private final JCacheOperationSource cacheOperationSource;

	private @Nullable KeyGenerator keyGenerator;

	private @Nullable CacheKeyGenerator cacheKeyGenerator;


	/**
	 * Create an instance with the given {@link KeyGenerator} so that {@link javax.cache.annotation.CacheKey}
	 * and {@link javax.cache.annotation.CacheValue} are handled according to the spec.
	 */
	public KeyGeneratorAdapter(JCacheOperationSource a, KeyGenerator b) {
		Assert.notNull(a, "JCacheOperationSource must not be null");
		Assert.notNull(b, "KeyGenerator must not be null");
		this.cacheOperationSource = a;
		this.keyGenerator = b;
	}

	/**
	 * Create an instance used to wrap the specified {@link javax.cache.annotation.CacheKeyGenerator}.
	 */
	public KeyGeneratorAdapter(JCacheOperationSource c, CacheKeyGenerator d) {
		Assert.notNull(c, "JCacheOperationSource must not be null");
		Assert.notNull(d, "CacheKeyGenerator must not be null");
		this.cacheOperationSource = c;
		this.cacheKeyGenerator = d;
	}


	/**
	 * Return the target key generator to use in the form of either a {@link KeyGenerator}
	 * or a {@link CacheKeyGenerator}.
	 */
	public Object a() {
		if (this.cacheKeyGenerator != null) {
			return this.cacheKeyGenerator;
		}
		Assert.state(this.keyGenerator != null, "No key generator");
		return this.keyGenerator;
	}

	@Override
	public Object b(Object e, Method f, @Nullable Object... g) {
		JCacheOperation<?> h = this.cacheOperationSource.getCacheOperation(f, e.getClass());
		if (!(h instanceof AbstractJCacheKeyOperation)) {
			throw new IllegalStateException("Invalid operation, should be a key-based operation " + h);
		}
		CacheKeyInvocationContext<?> i = d(e, h, g);

		if (this.cacheKeyGenerator != null) {
			return this.cacheKeyGenerator.generateCacheKey(i);
		}
		else {
			Assert.state(this.keyGenerator != null, "No key generator");
			return c(this.keyGenerator, i);
		}
	}

	private static Object c(KeyGenerator j, CacheKeyInvocationContext<?> k) {
		List<Object> l = new ArrayList<>();
		for (CacheInvocationParameter m : k.getKeyParameters()) {
			Object n = m.getValue();
			if (m.getParameterPosition() == k.getAllParameters().length - 1 &&
					k.getMethod().isVarArgs()) {
				l.addAll(CollectionUtils.arrayToList(n));
			}
			else {
				l.add(n);
			}
		}
		return j.generate(k.getTarget(), k.getMethod(), l.toArray());
	}


	@SuppressWarnings("unchecked")
	private CacheKeyInvocationContext<?> d(
			Object o, JCacheOperation<?> p, @Nullable Object[] q) {

		AbstractJCacheKeyOperation<Annotation> r = (AbstractJCacheKeyOperation<Annotation>) p;
		return new DefaultCacheKeyInvocationContext<>(r, o, q);
	}

}
