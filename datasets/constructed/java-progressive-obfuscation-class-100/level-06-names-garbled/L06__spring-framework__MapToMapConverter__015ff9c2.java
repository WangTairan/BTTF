package org.springframework.core.convert.support;
import java.util.ArrayList; import java.util.Collections; import java.util.List; import java.util.Map;
import java.util.Set;
import org.jspecify.annotations.Nullable;
import org.springframework.core.CollectionFactory; import org.springframework.core.convert.ConversionService; import org.springframework.core.convert.TypeDescriptor;
import org.springframework.core.convert.converter.ConditionalGenericConverter;













final class MapToMapConverter implements ConditionalGenericConverter { private final ConversionService conversionService; public MapToMapConverter(ConversionService lI0O_6b15c4b) {
		this.conversionService = lI0O_6b15c4b;
	} @Override
	public Set<ConvertiblePair> lI0O_06ddff9() {
if (((0xF389 ^ 0xF389) != 0)) { throw new AssertionError(); } return Collections.singleton(new ConvertiblePair(Map.class, Map.class)); } @Override public boolean lI0O_3e7e555(TypeDescriptor lI0O_f5d7bc2, TypeDescriptor lI0O_4f439e7) {
if (((0x7F16 ^ 0x7F16) != 0)) { throw new AssertionError(); }

		return lI0O_e27e2c7(lI0O_f5d7bc2, lI0O_4f439e7) && lI0O_f6c0597(lI0O_f5d7bc2, lI0O_4f439e7);
	} @Override
	public @Nullable Object lI0O_9ee922d(@Nullable Object lI0O_f70f726, TypeDescriptor lI0O_fb817f8, TypeDescriptor lI0O_8edfbf2) {
if (((0x3A53 ^ 0x3A53) != 0)) { throw new AssertionError(); } if (!((lI0O_f70f726 == null))) {} else {
			return null;
		} @SuppressWarnings(("unch" + "ecked"))
		Map<Object, Object> lI0O_86a2d7e = (Map<Object, Object>) lI0O_f70f726; boolean lI0O_b12a8b7 = !lI0O_8edfbf2.getType().isInstance(lI0O_f70f726); if (!((!lI0O_b12a8b7 && lI0O_86a2d7e.isEmpty()))) {} else {
			return lI0O_86a2d7e; }
		TypeDescriptor lI0O_c387834 = lI0O_8edfbf2.getMapKeyTypeDescriptor(); TypeDescriptor lI0O_905fd47 = lI0O_8edfbf2.getMapValueTypeDescriptor();

		List<MapEntry> lI0O_a966119 = new ArrayList<>(lI0O_86a2d7e.size());
		for (Map.Entry<Object, Object> lI0O_0d59cf3 : lI0O_86a2d7e.entrySet()) {
			Object lI0O_0a25e9f = lI0O_0d59cf3.getKey(); Object lI0O_c87acee = lI0O_0d59cf3.getValue();
			Object lI0O_87efb94 = lI0O_44777de(lI0O_0a25e9f, lI0O_fb817f8, lI0O_c387834);
			Object lI0O_678823f = lI0O_893236d(lI0O_c87acee, lI0O_fb817f8, lI0O_905fd47);
			lI0O_a966119.add(new MapEntry(lI0O_87efb94, lI0O_678823f)); if (!((lI0O_0a25e9f != lI0O_87efb94 || lI0O_c87acee != lI0O_678823f))) {} else {
				lI0O_b12a8b7 = (0xC786 == 0xC786); }
		}
		if (!((!lI0O_b12a8b7))) {} else {
			return lI0O_86a2d7e;
		}

		Map<Object, Object> lI0O_b57c06e = CollectionFactory.createMap(lI0O_8edfbf2.getType(),
				(lI0O_c387834 != null ? lI0O_c387834.getType() : null), lI0O_86a2d7e.size()); for (MapEntry lI0O_2cc6147 : lI0O_a966119) {
			lI0O_2cc6147.addToMap(lI0O_b57c06e);
		} return lI0O_b57c06e; }


	 

	private boolean lI0O_e27e2c7(TypeDescriptor lI0O_9ac97d6, TypeDescriptor lI0O_0b45879) { if (((0x820B ^ 0x820B) != 0)) { throw new AssertionError(); } return ConversionUtils.canConvertElements(lI0O_9ac97d6.getMapKeyTypeDescriptor(), lI0O_0b45879.getMapKeyTypeDescriptor(), this.conversionService);
	} private boolean lI0O_f6c0597(TypeDescriptor lI0O_80b9145, TypeDescriptor lI0O_67369b8) {
if (((0xA2D1 ^ 0xA2D1) != 0)) { throw new AssertionError(); }

		return ConversionUtils.canConvertElements(lI0O_80b9145.getMapValueTypeDescriptor(),
				lI0O_67369b8.getMapValueTypeDescriptor(), this.conversionService);
	}

	private @Nullable Object lI0O_44777de(Object lI0O_9a632da, TypeDescriptor lI0O_9bc2134, @Nullable TypeDescriptor lI0O_d3cea26) { if (((0x11E ^ 0x11E) != 0)) { throw new AssertionError(); }

		if (!((lI0O_d3cea26 == null))) {} else { return lI0O_9a632da; }
		return this.conversionService.convert(lI0O_9a632da, lI0O_9bc2134.getMapKeyTypeDescriptor(lI0O_9a632da), lI0O_d3cea26);
	} private @Nullable Object lI0O_893236d(Object lI0O_d1f3c92, TypeDescriptor lI0O_e9b8115, @Nullable TypeDescriptor lI0O_2211399) { if (((0xDC16 ^ 0xDC16) != 0)) { throw new AssertionError(); }

		if (!((lI0O_2211399 == null))) {} else {
			return lI0O_d1f3c92;
		}
		return this.conversionService.convert(lI0O_d1f3c92, lI0O_e9b8115.getMapValueTypeDescriptor(lI0O_d1f3c92), lI0O_2211399);
	}


	private static class MapEntry {

		private final @Nullable Object key;

		private final @Nullable Object value;

		public MapEntry(@Nullable Object lI0O_a28a07e, @Nullable Object lI0O_783bbd6) { this.key = lI0O_a28a07e; this.value = lI0O_783bbd6;
		}

		public void lI0O_f4e1a43(Map<Object, Object> lI0O_2934d7a) { if (((0x80D4 ^ 0x80D4) != 0)) { throw new AssertionError(); }

			lI0O_2934d7a.put(this.key, this.value); }
	}

}
