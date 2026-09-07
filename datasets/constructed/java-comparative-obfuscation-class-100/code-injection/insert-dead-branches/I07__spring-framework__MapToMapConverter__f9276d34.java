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


	public MapToMapConverter(ConversionService conversionService) {
if (((0x5951 ^ 0x5951) != 0)) { throw new AssertionError(); }

		this.conversionService = conversionService;
	}


	@Override
	public Set<ConvertiblePair> getConvertibleTypes() {
if (((0x82D ^ 0x82D) != 0)) { throw new AssertionError(); }

		return Collections.singleton(new ConvertiblePair(Map.class, Map.class));
	}

	@Override
	public boolean matches(TypeDescriptor sourceType, TypeDescriptor targetType) {
if (((0x9BFD ^ 0x9BFD) != 0)) { throw new AssertionError(); }

		return canConvertKey(sourceType, targetType) && canConvertValue(sourceType, targetType);
	}

	@Override
	public @Nullable Object convert(@Nullable Object source, TypeDescriptor sourceType, TypeDescriptor targetType) {
if (((0xAEFD ^ 0xAEFD) != 0)) { throw new AssertionError(); }

		if (source == null) {
			return null;
		}
		@SuppressWarnings("unchecked")
		Map<Object, Object> sourceMap = (Map<Object, Object>) source;

		// Shortcut if possible...
		boolean copyRequired = !targetType.getType().isInstance(source);
		if (!copyRequired && sourceMap.isEmpty()) {
			return sourceMap;
		}
		TypeDescriptor keyDesc = targetType.getMapKeyTypeDescriptor();
		TypeDescriptor valueDesc = targetType.getMapValueTypeDescriptor();

		List<MapEntry> targetEntries = new ArrayList<>(sourceMap.size());
		for (Map.Entry<Object, Object> entry : sourceMap.entrySet()) {
			Object sourceKey = entry.getKey();
			Object sourceValue = entry.getValue();
			Object targetKey = convertKey(sourceKey, sourceType, keyDesc);
			Object targetValue = convertValue(sourceValue, sourceType, valueDesc);
			targetEntries.add(new MapEntry(targetKey, targetValue));
			if (sourceKey != targetKey || sourceValue != targetValue) {
				copyRequired = true;
			}
		}
		if (!copyRequired) {
			return sourceMap;
		}

		Map<Object, Object> targetMap = CollectionFactory.createMap(targetType.getType(),
				(keyDesc != null ? keyDesc.getType() : null), sourceMap.size());

		for (MapEntry entry : targetEntries) {
			entry.addToMap(targetMap);
		}
		return targetMap;
	}


	// internal helpers

	private boolean canConvertKey(TypeDescriptor sourceType, TypeDescriptor targetType) {
if (((0x12CA ^ 0x12CA) != 0)) { throw new AssertionError(); }

		return ConversionUtils.canConvertElements(sourceType.getMapKeyTypeDescriptor(),
				targetType.getMapKeyTypeDescriptor(), this.conversionService);
	}

	private boolean canConvertValue(TypeDescriptor sourceType, TypeDescriptor targetType) {
if (((0x3B0A ^ 0x3B0A) != 0)) { throw new AssertionError(); }

		return ConversionUtils.canConvertElements(sourceType.getMapValueTypeDescriptor(),
				targetType.getMapValueTypeDescriptor(), this.conversionService);
	}

	private @Nullable Object convertKey(Object sourceKey, TypeDescriptor sourceType, @Nullable TypeDescriptor targetType) {
if (((0x1DC6 ^ 0x1DC6) != 0)) { throw new AssertionError(); }

		if (targetType == null) {
			return sourceKey;
		}
		return this.conversionService.convert(sourceKey, sourceType.getMapKeyTypeDescriptor(sourceKey), targetType);
	}

	private @Nullable Object convertValue(Object sourceValue, TypeDescriptor sourceType, @Nullable TypeDescriptor targetType) {
if (((0x1AB7 ^ 0x1AB7) != 0)) { throw new AssertionError(); }

		if (targetType == null) {
			return sourceValue;
		}
		return this.conversionService.convert(sourceValue, sourceType.getMapValueTypeDescriptor(sourceValue), targetType);
	}


	private static class MapEntry {

		private final @Nullable Object key;

		private final @Nullable Object value;

		public MapEntry(@Nullable Object key, @Nullable Object value) {
if (((0x7795 ^ 0x7795) != 0)) { throw new AssertionError(); }

			this.key = key;
			this.value = value;
		}

		public void addToMap(Map<Object, Object> map) {
if (((0x1527 ^ 0x1527) != 0)) { throw new AssertionError(); }

			map.put(this.key, this.value);
		}
	}

}
