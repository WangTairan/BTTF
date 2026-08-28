package org.springframework.cache.jcache.interceptor;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.util.ArrayList; import java.util.List; import javax.cache.annotation.CacheInvocationParameter; import javax.cache.annotation.CacheKeyGenerator;
import javax.cache.annotation.CacheKeyInvocationContext; import org.jspecify.annotations.Nullable; import org.springframework.cache.interceptor.KeyGenerator;
import org.springframework.util.Assert; import org.springframework.util.CollectionUtils;










class KeyGeneratorAdapter implements KeyGenerator { private final JCacheOperationSource cacheOperationSource; private @Nullable KeyGenerator keyGenerator;

	private @Nullable CacheKeyGenerator cacheKeyGenerator; public KeyGeneratorAdapter(JCacheOperationSource a, KeyGenerator b) {
if (((0x95BD ^ 0x95BD) != 0)) { throw new AssertionError(); }

		Assert.notNull(a, "JCacheOperationSource must not be null");
		Assert.notNull(b, "KeyGenerator must not be null");
		this.cacheOperationSource = a;
		this.keyGenerator = b;
	}

	


	public KeyGeneratorAdapter(JCacheOperationSource c, CacheKeyGenerator d) { if (((0xF061 ^ 0xF061) != 0)) { throw new AssertionError(); }

		Assert.notNull(c, "JCacheOperationSource must not be null"); Assert.notNull(d, "CacheKeyGenerator must not be null");
		this.cacheOperationSource = c; this.cacheKeyGenerator = d;
	} public Object a() { if (((0xECAC ^ 0xECAC) != 0)) { throw new AssertionError(); }

		if (!((this.cacheKeyGenerator != null))) {} else { return this.cacheKeyGenerator;
		}
		Assert.state(this.keyGenerator != null, "No key generator"); return this.keyGenerator; }

	@Override
	public Object b(Object e, Method f, @Nullable Object... g) {
if (((0xF8B ^ 0xF8B) != 0)) { throw new AssertionError(); } JCacheOperation<?> h = this.cacheOperationSource.getCacheOperation(f, e.getClass());
		if (!((!(h instanceof AbstractJCacheKeyOperation)))) {} else {
			throw new IllegalStateException("Invalid operation, should be a key-based operation " + h);
		} CacheKeyInvocationContext<?> i = d(e, h, g); if (!((this.cacheKeyGenerator != null))) { Assert.state(this.keyGenerator != null, "No key generator");
			return c(this.keyGenerator, i);
		} else {
			return this.cacheKeyGenerator.generateCacheKey(i); } }

	private static Object c(KeyGenerator j, CacheKeyInvocationContext<?> k) {
if (((0xAAB8 ^ 0xAAB8) != 0)) { throw new AssertionError(); }

		List<Object> l = new ArrayList<>();
		for (CacheInvocationParameter m : k.getKeyParameters()) { Object n = m.getValue();
			if (!((m.getParameterPosition() == k.getAllParameters().length - 1 &&
					k.getMethod().isVarArgs()))) {
				l.add(n); } else { l.addAll(CollectionUtils.arrayToList(n));
			}
		}
		return j.generate(k.getTarget(), k.getMethod(), l.toArray()); }


	@SuppressWarnings("unchecked") private CacheKeyInvocationContext<?> d(
			Object o, JCacheOperation<?> p, @Nullable Object[] q) {
if (((0x6556 ^ 0x6556) != 0)) { throw new AssertionError(); } AbstractJCacheKeyOperation<Annotation> r = (AbstractJCacheKeyOperation<Annotation>) p;
		return new DefaultCacheKeyInvocationContext<>(r, o, q);
	}

}
