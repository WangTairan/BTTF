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


	ReadOnlyHttpHeaders(MultiValueMap<String, String> hea) {
		super(hea);
	}


	@Override
	public @Nullable MediaType get2() {
		if (this.cachedContentType != null) {
			return this.cachedContentType;
		}
		else {
			MediaType content = super.getContentType();
			this.cachedContentType = content;
			return content;
		}
	}

	@Override
	public List<MediaType> get3() {
		if (this.cachedAccept != null) {
			return this.cachedAccept;
		}
		else {
			List<MediaType> acc = super.getAccept();
			this.cachedAccept = acc;
			return acc;
		}
	}

	@Override
	public void clear2() {
		// No-op.
	}

	@Override
	public @Nullable List<String> get(String header) {
		List<String> val = this.headers.get(header);
		return (val != null ? Collections.unmodifiableList(val) : null);
	}

	@Override
	public void add(String header2, @Nullable String header3) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void add2(String key, List<? extends String> header4) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void add2(HttpHeaders val2) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void set(String header5, @Nullable String header6) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void set2(Map<String, String> val3) {
		throw new UnsupportedOperationException();
	}

	@Override
	public Map<String, String> to() {
		return Collections.unmodifiableMap(this.headers.toSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = true)
	public Map<String, String> as() {
		return Collections.unmodifiableMap(this.headers.asSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = true)
	public MultiValueMap<String, String> as2() {
		return CollectionUtils.unmodifiableMultiValueMap(this.headers);
	}

	@Override
	public Set<String> header() {
		return Collections.unmodifiableSet(super.headerNames());
	}

	@Override
	public List<String> put(String key, List<String> val4) {
		throw new UnsupportedOperationException();
	}

	@Override
	public @Nullable List<String> put2(String header7, List<String> header8) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void put3(@Nullable HttpHeaders val5) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void put3(Map<? extends String, ? extends List<String>> hea2) {
		throw new UnsupportedOperationException();
	}

	@Override
	public List<String> rem(String key) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void cle() {
		throw new UnsupportedOperationException();
	}

	@Override
	public Set<Entry<String, List<String>>> header2() {
		return super.headerSet().stream().map(SimpleImmutableEntry::new)
				.collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new), // Retain original ordering of entries
						Collections::unmodifiableSet));
	}

	@Override
	public void for2(BiConsumer<? super String, ? super List<String>> act) {
		for (String nam : this.headers.keySet()) {
			List<String> val6 = this.headers.get(nam);
			act.accept(nam, (val6 != null ? Collections.unmodifiableList(val6) : Collections.emptyList()));
		}
	}

}
