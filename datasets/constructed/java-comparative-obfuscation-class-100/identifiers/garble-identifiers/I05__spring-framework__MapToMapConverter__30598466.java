package org.springframework.core.convert.support;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.jspecify.annotations.Nullable;
import org.springframework.core.CollectionFactory;
import org.springframework.core.convert.ConversionService;
import org.springframework.core.convert.TypeDescriptor;
import org.springframework.core.convert.converter.ConditionalGenericConverter;

/**
 * Converts a Map to another Map.
 *
 * <p>First, creates a new Map of the requested targetType with a size equal to the
 * size of the source Map. Then copies each element in the source map to the target map.
 * Will perform a conversion from the source map's parameterized K,V types to the target
 * map's parameterized types K,V if necessary.
 *
 * @author Keith Donald
 * @author Juergen Hoeller
 * @since 3.0
 */
final class MapToMapConverter implements ConditionalGenericConverter {

	private final ConversionService conversionService;


	public MapToMapConverter(ConversionService a) {
		this.conversionService = a;
	}


	@Override
	public Set<ConvertiblePair> a() {
		return Collections.singleton(new ConvertiblePair(Map.class, Map.class));
	}

	@Override
	public boolean b(TypeDescriptor b, TypeDescriptor c) {
		return d(b, c) && e(b, c);
	}

	@Override
	public @Nullable Object c(@Nullable Object d, TypeDescriptor e, TypeDescriptor f) {
		if (d == null) {
			return null;
		}
		@SuppressWarnings("unchecked")
		Map<Object, Object> g = (Map<Object, Object>) d;

		// Shortcut if possible...
		boolean h = !f.getType().isInstance(d);
		if (!h && g.isEmpty()) {
			return g;
		}
		TypeDescriptor i = f.getMapKeyTypeDescriptor();
		TypeDescriptor j = f.getMapValueTypeDescriptor();

		List<MapEntry> k = new ArrayList<>(g.size());
		for (Map.Entry<Object, Object> l : g.entrySet()) {
			Object m = l.getKey();
			Object n = l.getValue();
			Object o = f(m, e, i);
			Object p = g(n, e, j);
			k.add(new MapEntry(o, p));
			if (m != o || n != p) {
				h = true;
			}
		}
		if (!h) {
			return g;
		}

		Map<Object, Object> q = CollectionFactory.createMap(f.getType(),
				(i != null ? i.getType() : null), g.size());

		for (MapEntry r : k) {
			r.addToMap(q);
		}
		return q;
	}


	// internal helpers

	private boolean d(TypeDescriptor s, TypeDescriptor t) {
		return ConversionUtils.canConvertElements(s.getMapKeyTypeDescriptor(),
				t.getMapKeyTypeDescriptor(), this.conversionService);
	}

	private boolean e(TypeDescriptor u, TypeDescriptor v) {
		return ConversionUtils.canConvertElements(u.getMapValueTypeDescriptor(),
				v.getMapValueTypeDescriptor(), this.conversionService);
	}

	private @Nullable Object f(Object w, TypeDescriptor x, @Nullable TypeDescriptor y) {
		if (y == null) {
			return w;
		}
		return this.conversionService.convert(w, x.getMapKeyTypeDescriptor(w), y);
	}

	private @Nullable Object g(Object z, TypeDescriptor A, @Nullable TypeDescriptor B) {
		if (B == null) {
			return z;
		}
		return this.conversionService.convert(z, A.getMapValueTypeDescriptor(z), B);
	}


	private static class MapEntry {

		private final @Nullable Object key;

		private final @Nullable Object value;

		public MapEntry(@Nullable Object C, @Nullable Object D) {
			this.key = C;
			this.value = D;
		}

		public void a(Map<Object, Object> E) {
			E.put(this.key, this.value);
		}
	}

}
