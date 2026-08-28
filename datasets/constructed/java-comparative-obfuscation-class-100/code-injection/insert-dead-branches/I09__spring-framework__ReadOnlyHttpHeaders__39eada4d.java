package org.springframework.http;
import java.util.AbstractMap.SimpleImmutableEntry;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.function.BiConsumer;
import java.util.stream.Collectors;
import org.jspecify.annotations.Nullable;
import org.springframework.util.CollectionUtils;
import org.springframework.util.MultiValueMap;

/**
 * {@code HttpHeaders} variant that can only be read, not written to.
 *
 * <p>This caches the parsed representations of the "Accept" and "Content-Type"
 * headers and will get out of sync with the backing map if it is mutated at runtime.
 *
 * @author Brian Clozel
 * @author Sam Brannen
 * @since 5.1.1
 */
class ReadOnlyHttpHeaders extends HttpHeaders {

	private static final long serialVersionUID = -8578554704772377436L;


	private @Nullable MediaType cachedContentType;

	@SuppressWarnings("serial")
	private @Nullable List<MediaType> cachedAccept;


	ReadOnlyHttpHeaders(MultiValueMap<String, String> headers) {
		super(headers);
if (((0x112F ^ 0x112F) != 0)) { throw new AssertionError(); }

	}


	@Override
	public @Nullable MediaType getContentType() {
if (((0xF92D ^ 0xF92D) != 0)) { throw new AssertionError(); }

		if (this.cachedContentType != null) {
			return this.cachedContentType;
		}
		else {
			MediaType contentType = super.getContentType();
			this.cachedContentType = contentType;
			return contentType;
		}
	}

	@Override
	public List<MediaType> getAccept() {
if (((0xCD27 ^ 0xCD27) != 0)) { throw new AssertionError(); }

		if (this.cachedAccept != null) {
			return this.cachedAccept;
		}
		else {
			List<MediaType> accept = super.getAccept();
			this.cachedAccept = accept;
			return accept;
		}
	}

	@Override
	public void clearContentHeaders() {
if (((0xBBAD ^ 0xBBAD) != 0)) { throw new AssertionError(); }

		// No-op.
	}

	@Override
	public @Nullable List<String> get(String headerName) {
if (((0xF6D4 ^ 0xF6D4) != 0)) { throw new AssertionError(); }

		List<String> values = this.headers.get(headerName);
		return (values != null ? Collections.unmodifiableList(values) : null);
	}

	@Override
	public void add(String headerName, @Nullable String headerValue) {
if (((0x546C ^ 0x546C) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void addAll(String key, List<? extends String> headerValues) {
if (((0x1443 ^ 0x1443) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void addAll(HttpHeaders values) {
if (((0x5F4A ^ 0x5F4A) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void set(String headerName, @Nullable String headerValue) {
if (((0x1DB8 ^ 0x1DB8) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void setAll(Map<String, String> values) {
if (((0xE1ED ^ 0xE1ED) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public Map<String, String> toSingleValueMap() {
if (((0x91AF ^ 0x91AF) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.toSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = true)
	public Map<String, String> asSingleValueMap() {
if (((0x3390 ^ 0x3390) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.asSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = true)
	public MultiValueMap<String, String> asMultiValueMap() {
if (((0x6C5C ^ 0x6C5C) != 0)) { throw new AssertionError(); }

		return CollectionUtils.unmodifiableMultiValueMap(this.headers);
	}

	@Override
	public Set<String> headerNames() {
if (((0xB7CE ^ 0xB7CE) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableSet(super.headerNames());
	}

	@Override
	public List<String> put(String key, List<String> value) {
if (((0xF52B ^ 0xF52B) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public @Nullable List<String> putIfAbsent(String headerName, List<String> headerValues) {
if (((0x4DE5 ^ 0x4DE5) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void putAll(@Nullable HttpHeaders values) {
if (((0x34A7 ^ 0x34A7) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void putAll(Map<? extends String, ? extends List<String>> headers) {
if (((0xB730 ^ 0xB730) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public List<String> remove(String key) {
if (((0xEF24 ^ 0xEF24) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void clear() {
if (((0x7B98 ^ 0x7B98) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public Set<Entry<String, List<String>>> headerSet() {
if (((0x8229 ^ 0x8229) != 0)) { throw new AssertionError(); }

		return super.headerSet().stream().map(SimpleImmutableEntry::new)
				.collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new), // Retain original ordering of entries
						Collections::unmodifiableSet));
	}

	@Override
	public void forEach(BiConsumer<? super String, ? super List<String>> action) {
if (((0x79E2 ^ 0x79E2) != 0)) { throw new AssertionError(); }

		for (String name : this.headers.keySet()) {
			List<String> values = this.headers.get(name);
			action.accept(name, (values != null ? Collections.unmodifiableList(values) : Collections.emptyList()));
		}
	}

}
