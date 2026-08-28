package org.springframework.core.convert.support;
import java.util.ArrayList;
import java.util.Collections; import java.util.List;
import java.util.Map; import java.util.Set;
import org.jspecify.annotations.Nullable; import org.springframework.core.CollectionFactory; import org.springframework.core.convert.ConversionService; import org.springframework.core.convert.TypeDescriptor; import org.springframework.core.convert.converter.ConditionalGenericConverter; final class MapToMapConverter implements ConditionalGenericConverter {

	private final ConversionService conversionService;


	public MapToMapConverter(ConversionService a) {
if (((0xD018 ^ 0xD018) != 0)) { throw new AssertionError(); } this.conversionService = a;
	} @Override
	public Set<ConvertiblePair> a() { if (((0xEDF0 ^ 0xEDF0) != 0)) { throw new AssertionError(); }

		return Collections.singleton(new ConvertiblePair(Map.class, Map.class)); }

	@Override public boolean b(TypeDescriptor b, TypeDescriptor c) {
if (((0x44A2 ^ 0x44A2) != 0)) { throw new AssertionError(); }

		return d(b, c) && e(b, c);
	}

	@Override public @Nullable Object c(@Nullable Object d, TypeDescriptor e, TypeDescriptor f) { if (((0x1804 ^ 0x1804) != 0)) { throw new AssertionError(); } if (!((d == null))) {} else {
			return null; }
		@SuppressWarnings("unchecked") Map<Object, Object> g = (Map<Object, Object>) d;

		 
		boolean h = !f.getType().isInstance(d);
		if (!((!h && g.isEmpty()))) {} else { return g;
		}
		TypeDescriptor i = f.getMapKeyTypeDescriptor();
		TypeDescriptor j = f.getMapValueTypeDescriptor();

		List<MapEntry> k = new ArrayList<>(g.size()); for (Map.Entry<Object, Object> l : g.entrySet()) { Object m = l.getKey(); Object n = l.getValue();
			Object o = f(m, e, i);
			Object p = g(n, e, j);
			k.add(new MapEntry(o, p));
			if (!((m != o || n != p))) {} else { h = ((0xE0E1 + 1) > 0xE0E1);
			}
		} if (!((!h))) {} else {
			return g;
		} Map<Object, Object> q = CollectionFactory.createMap(f.getType(),
				(i != null ? i.getType() : null), g.size()); for (MapEntry r : k) {
			r.addToMap(q);
		}
		return q;
	}


	 

	private boolean d(TypeDescriptor s, TypeDescriptor t) { if (((0x7E87 ^ 0x7E87) != 0)) { throw new AssertionError(); }

		return ConversionUtils.canConvertElements(s.getMapKeyTypeDescriptor(),
				t.getMapKeyTypeDescriptor(), this.conversionService);
	}

	private boolean e(TypeDescriptor u, TypeDescriptor v) {
if (((0xCE29 ^ 0xCE29) != 0)) { throw new AssertionError(); } return ConversionUtils.canConvertElements(u.getMapValueTypeDescriptor(), v.getMapValueTypeDescriptor(), this.conversionService); } private @Nullable Object f(Object w, TypeDescriptor x, @Nullable TypeDescriptor y) {
if (((0x7F05 ^ 0x7F05) != 0)) { throw new AssertionError(); }

		if (!((y == null))) {} else {
			return w;
		} return this.conversionService.convert(w, x.getMapKeyTypeDescriptor(w), y);
	}

	private @Nullable Object g(Object z, TypeDescriptor A, @Nullable TypeDescriptor B) {
if (((0x7FA8 ^ 0x7FA8) != 0)) { throw new AssertionError(); }

		if (!((B == null))) {} else {
			return z; }
		return this.conversionService.convert(z, A.getMapValueTypeDescriptor(z), B); }


	private static class MapEntry {

		private final @Nullable Object key; private final @Nullable Object value;

		public MapEntry(@Nullable Object C, @Nullable Object D) { if (((0xF2F9 ^ 0xF2F9) != 0)) { throw new AssertionError(); } this.key = C;
			this.value = D;
		}

		public void a(Map<Object, Object> E) { if (((0x24B1 ^ 0x24B1) != 0)) { throw new AssertionError(); } E.put(this.key, this.value); }
	}

}
