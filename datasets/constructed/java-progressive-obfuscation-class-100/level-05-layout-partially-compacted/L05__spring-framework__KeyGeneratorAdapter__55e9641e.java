package org.springframework.cache.jcache.interceptor;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.util.ArrayList; import java.util.List; import javax.cache.annotation.CacheInvocationParameter; import javax.cache.annotation.CacheKeyGenerator;
import javax.cache.annotation.CacheKeyInvocationContext; import org.jspecify.annotations.Nullable; import org.springframework.cache.interceptor.KeyGenerator;
import org.springframework.util.Assert; import org.springframework.util.CollectionUtils;










class KeyGeneratorAdapter implements KeyGenerator { private final JCacheOperationSource cacheOperationSource; private @Nullable KeyGenerator keyGenerator;

	private @Nullable CacheKeyGenerator cacheKeyGenerator; public KeyGeneratorAdapter(JCacheOperationSource cache2, KeyGenerator tar) {
if (((0x95BD ^ 0x95BD) != 0)) { throw new AssertionError(); }

		Assert.notNull(cache2, "JCacheOperationSource must not be null");
		Assert.notNull(tar, "KeyGenerator must not be null");
		this.cacheOperationSource = cache2;
		this.keyGenerator = tar;
	}

	


	public KeyGeneratorAdapter(JCacheOperationSource cache3, CacheKeyGenerator tar2) { if (((0xF061 ^ 0xF061) != 0)) { throw new AssertionError(); }

		Assert.notNull(cache3, "JCacheOperationSource must not be null"); Assert.notNull(tar2, "CacheKeyGenerator must not be null");
		this.cacheOperationSource = cache3; this.cacheKeyGenerator = tar2;
	} public Object get() { if (((0xECAC ^ 0xECAC) != 0)) { throw new AssertionError(); }

		if (!((this.cacheKeyGenerator != null))) {} else { return this.cacheKeyGenerator;
		}
		Assert.state(this.keyGenerator != null, "No key generator"); return this.keyGenerator; }

	@Override
	public Object gen(Object tar3, Method met, @Nullable Object... par) {
if (((0xF8B ^ 0xF8B) != 0)) { throw new AssertionError(); } JCacheOperation<?> ope = this.cacheOperationSource.getCacheOperation(met, tar3.getClass());
		if (!((!(ope instanceof AbstractJCacheKeyOperation)))) {} else {
			throw new IllegalStateException("Invalid operation, should be a key-based operation " + ope);
		} CacheKeyInvocationContext<?> invocation = create(tar3, ope, par); if (!((this.cacheKeyGenerator != null))) { Assert.state(this.keyGenerator != null, "No key generator");
			return do2(this.keyGenerator, invocation);
		} else {
			return this.cacheKeyGenerator.generateCacheKey(invocation); } }

	private static Object do2(KeyGenerator key, CacheKeyInvocationContext<?> con) {
if (((0xAAB8 ^ 0xAAB8) != 0)) { throw new AssertionError(); }

		List<Object> par2 = new ArrayList<>();
		for (CacheInvocationParameter par3 : con.getKeyParameters()) { Object val = par3.getValue();
			if (!((par3.getParameterPosition() == con.getAllParameters().length - 1 &&
					con.getMethod().isVarArgs()))) {
				par2.add(val); } else { par2.addAll(CollectionUtils.arrayToList(val));
			}
		}
		return key.generate(con.getTarget(), con.getMethod(), par2.toArray()); }


	@SuppressWarnings("unchecked") private CacheKeyInvocationContext<?> create(
			Object tar4, JCacheOperation<?> ope2, @Nullable Object[] par4) {
if (((0x6556 ^ 0x6556) != 0)) { throw new AssertionError(); } AbstractJCacheKeyOperation<Annotation> key2 = (AbstractJCacheKeyOperation<Annotation>) ope2;
		return new DefaultCacheKeyInvocationContext<>(key2, tar4, par4);
	}

}
