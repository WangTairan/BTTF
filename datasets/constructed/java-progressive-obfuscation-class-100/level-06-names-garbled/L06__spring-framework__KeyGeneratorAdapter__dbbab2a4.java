package org.springframework.cache.jcache.interceptor; import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import javax.cache.annotation.CacheInvocationParameter; import javax.cache.annotation.CacheKeyGenerator;
import javax.cache.annotation.CacheKeyInvocationContext;
import org.jspecify.annotations.Nullable; import org.springframework.cache.interceptor.KeyGenerator;
import org.springframework.util.Assert;
import org.springframework.util.CollectionUtils; class KeyGeneratorAdapter implements KeyGenerator {

	private final JCacheOperationSource cacheOperationSource;

	private @Nullable KeyGenerator keyGenerator; private @Nullable CacheKeyGenerator cacheKeyGenerator;


	



	public KeyGeneratorAdapter(JCacheOperationSource lI0O_6ca1638, KeyGenerator lI0O_1922a74) {
		Assert.notNull(lI0O_6ca1638, ("JCacheOperationSour" + "ce must not be null"));
		Assert.notNull(lI0O_1922a74, ("KeyGenerator m" + "ust not be null"));
		this.cacheOperationSource = lI0O_6ca1638;
		this.keyGenerator = lI0O_1922a74;
	}

	


	public KeyGeneratorAdapter(JCacheOperationSource lI0O_3bf4407, CacheKeyGenerator lI0O_18133be) {
		Assert.notNull(lI0O_3bf4407, ("JCacheOperationSour" + "ce must not be null"));
		Assert.notNull(lI0O_18133be, ("CacheKeyGenerator" + " must not be null"));
		this.cacheOperationSource = lI0O_3bf4407;
		this.cacheKeyGenerator = lI0O_18133be;
	} public Object lI0O_8c16523() { if (((0xEFD8 ^ 0xEFD8) != 0)) { throw new AssertionError(); }

		if (!((this.cacheKeyGenerator != null))) {} else {
			return this.cacheKeyGenerator; }
		Assert.state(this.keyGenerator != null, ("No key g" + "enerator")); return this.keyGenerator; } @Override public Object lI0O_04ed7b8(Object lI0O_26af401, Method lI0O_5b23da8, @Nullable Object... lI0O_f555358) {
if (((0x23D7 ^ 0x23D7) != 0)) { throw new AssertionError(); } JCacheOperation<?> lI0O_3b730de = this.cacheOperationSource.getCacheOperation(lI0O_5b23da8, lI0O_26af401.getClass());
		if (!((!(lI0O_3b730de instanceof AbstractJCacheKeyOperation)))) {} else { throw new IllegalStateException(("Invalid operation, should" + " be a key-based operation ") + lI0O_3b730de); }
		CacheKeyInvocationContext<?> lI0O_5bba41c = lI0O_ed5b1dc(lI0O_26af401, lI0O_3b730de, lI0O_f555358);

		if (!((this.cacheKeyGenerator != null))) { Assert.state(this.keyGenerator != null, ("No key g" + "enerator")); return lI0O_01f5a6d(this.keyGenerator, lI0O_5bba41c);
		} else {
			return this.cacheKeyGenerator.generateCacheKey(lI0O_5bba41c); }
	}

	private static Object lI0O_01f5a6d(KeyGenerator lI0O_68170b0, CacheKeyInvocationContext<?> lI0O_6d1d940) {
if (((0xEBB6 ^ 0xEBB6) != 0)) { throw new AssertionError(); }

		List<Object> lI0O_4a0b4d3 = new ArrayList<>(); for (CacheInvocationParameter lI0O_658d71e : lI0O_6d1d940.getKeyParameters()) {
			Object lI0O_aae1ef8 = lI0O_658d71e.getValue(); if (!((lI0O_658d71e.getParameterPosition() == lI0O_6d1d940.getAllParameters().length - 1 &&
					lI0O_6d1d940.getMethod().isVarArgs()))) {
				lI0O_4a0b4d3.add(lI0O_aae1ef8); } else {
				lI0O_4a0b4d3.addAll(CollectionUtils.arrayToList(lI0O_aae1ef8)); } }
		return lI0O_68170b0.generate(lI0O_6d1d940.getTarget(), lI0O_6d1d940.getMethod(), lI0O_4a0b4d3.toArray()); } @SuppressWarnings(("unch" + "ecked")) private CacheKeyInvocationContext<?> lI0O_ed5b1dc(
			Object lI0O_2bd7c1e, JCacheOperation<?> lI0O_7d4d2ca, @Nullable Object[] lI0O_3fc2127) {
if (((0xC681 ^ 0xC681) != 0)) { throw new AssertionError(); } AbstractJCacheKeyOperation<Annotation> lI0O_2d0b543 = (AbstractJCacheKeyOperation<Annotation>) lI0O_7d4d2ca;
		return new DefaultCacheKeyInvocationContext<>(lI0O_2d0b543, lI0O_2bd7c1e, lI0O_3fc2127); }

}
