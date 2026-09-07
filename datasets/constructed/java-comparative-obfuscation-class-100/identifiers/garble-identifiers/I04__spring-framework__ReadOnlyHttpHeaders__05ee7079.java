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


	ReadOnlyHttpHeaders(MultiValueMap<String, String> a) {
		super(a);
	}


	@Override
	public @Nullable MediaType a() {
		if (this.cachedContentType != null) {
			return this.cachedContentType;
		}
		else {
			MediaType b = super.getContentType();
			this.cachedContentType = b;
			return b;
		}
	}

	@Override
	public List<MediaType> b() {
		if (this.cachedAccept != null) {
			return this.cachedAccept;
		}
		else {
			List<MediaType> c = super.getAccept();
			this.cachedAccept = c;
			return c;
		}
	}

	@Override
	public void c() {
		// No-op.
	}

	@Override
	public @Nullable List<String> d(String d) {
		List<String> e = this.headers.get(d);
		return (e != null ? Collections.unmodifiableList(e) : null);
	}

	@Override
	public void e(String f, @Nullable String g) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void f(String h, List<? extends String> i) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void f(HttpHeaders j) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void g(String k, @Nullable String l) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void h(Map<String, String> m) {
		throw new UnsupportedOperationException();
	}

	@Override
	public Map<String, String> i() {
		return Collections.unmodifiableMap(this.headers.toSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = true)
	public Map<String, String> j() {
		return Collections.unmodifiableMap(this.headers.asSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = true)
	public MultiValueMap<String, String> k() {
		return CollectionUtils.unmodifiableMultiValueMap(this.headers);
	}

	@Override
	public Set<String> l() {
		return Collections.unmodifiableSet(super.headerNames());
	}

	@Override
	public List<String> m(String n, List<String> o) {
		throw new UnsupportedOperationException();
	}

	@Override
	public @Nullable List<String> n(String p, List<String> q) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void o(@Nullable HttpHeaders r) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void o(Map<? extends String, ? extends List<String>> s) {
		throw new UnsupportedOperationException();
	}

	@Override
	public List<String> p(String t) {
		throw new UnsupportedOperationException();
	}

	@Override
	public void q() {
		throw new UnsupportedOperationException();
	}

	@Override
	public Set<Entry<String, List<String>>> r() {
		return super.headerSet().stream().map(SimpleImmutableEntry::new)
				.collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new), // Retain original ordering of entries
						Collections::unmodifiableSet));
	}

	@Override
	public void s(BiConsumer<? super String, ? super List<String>> u) {
		for (String v : this.headers.keySet()) {
			List<String> w = this.headers.get(v);
			u.accept(v, (w != null ? Collections.unmodifiableList(w) : Collections.emptyList()));
		}
	}

}
