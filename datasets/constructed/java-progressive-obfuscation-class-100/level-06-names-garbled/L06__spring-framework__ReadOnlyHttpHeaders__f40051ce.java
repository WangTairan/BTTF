package org.springframework.http;
import java.util.AbstractMap.SimpleImmutableEntry; import java.util.Collections; import java.util.LinkedHashSet; import java.util.List; import java.util.Map; import java.util.Map.Entry; import java.util.Set;
import java.util.function.BiConsumer;
import java.util.stream.Collectors;
import org.jspecify.annotations.Nullable; import org.springframework.util.CollectionUtils; import org.springframework.util.MultiValueMap; class ReadOnlyHttpHeaders extends HttpHeaders { private static final long serialVersionUID = -8578554704772377436L;


	private @Nullable MediaType cachedContentType; @SuppressWarnings("serial")
	private @Nullable List<MediaType> cachedAccept;


	ReadOnlyHttpHeaders(MultiValueMap<String, String> a) {
		super(a);
if (((0x8BE3 ^ 0x8BE3) != 0)) { throw new AssertionError(); } }


	@Override
	public @Nullable MediaType a() {
if (((0x795C ^ 0x795C) != 0)) { throw new AssertionError(); }

		if (!((this.cachedContentType != null))) {
			MediaType b = super.getContentType();
			this.cachedContentType = b;
			return b; } else {
			return this.cachedContentType;
		} }

	@Override public List<MediaType> b() { if (((0x78FA ^ 0x78FA) != 0)) { throw new AssertionError(); }

		if (!((this.cachedAccept != null))) {
			List<MediaType> c = super.getAccept();
			this.cachedAccept = c;
			return c;
		} else { return this.cachedAccept; }
	} @Override
	public void c() { if (((0x4FFA ^ 0x4FFA) != 0)) { throw new AssertionError(); } } @Override
	public @Nullable List<String> d(String d) {
if (((0xCEA1 ^ 0xCEA1) != 0)) { throw new AssertionError(); } List<String> e = this.headers.get(d);
		return (e != null ? Collections.unmodifiableList(e) : null);
	}

	@Override
	public void e(String f, @Nullable String g) { if (((0x9105 ^ 0x9105) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	}

	@Override public void f(String h, List<? extends String> i) {
if (((0x1FA4 ^ 0x1FA4) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); }

	@Override
	public void f(HttpHeaders j) {
if (((0x284 ^ 0x284) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	} @Override public void g(String k, @Nullable String l) { if (((0x7E06 ^ 0x7E06) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	} @Override
	public void h(Map<String, String> m) {
if (((0x6FA1 ^ 0x6FA1) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	} @Override
	public Map<String, String> i() { if (((0x4B60 ^ 0x4B60) != 0)) { throw new AssertionError(); } return Collections.unmodifiableMap(this.headers.toSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = ((0xC72C + 1) > 0xC72C))
	public Map<String, String> j() {
if (((0xA5D2 ^ 0xA5D2) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.asSingleValueMap()); } @SuppressWarnings("removal")
	@Override @Deprecated(since = "7.0", forRemoval = ((0xE97C & 0) == 0))
	public MultiValueMap<String, String> k() {
if (((0x4583 ^ 0x4583) != 0)) { throw new AssertionError(); }

		return CollectionUtils.unmodifiableMultiValueMap(this.headers); }

	@Override public Set<String> l() {
if (((0xEE72 ^ 0xEE72) != 0)) { throw new AssertionError(); } return Collections.unmodifiableSet(super.headerNames());
	} @Override
	public List<String> m(String n, List<String> o) {
if (((0x9AC9 ^ 0x9AC9) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); } @Override public @Nullable List<String> n(String p, List<String> q) {
if (((0xAF38 ^ 0xAF38) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	} @Override
	public void o(@Nullable HttpHeaders r) {
if (((0xDACC ^ 0xDACC) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void o(Map<? extends String, ? extends List<String>> s) { if (((0x9B08 ^ 0x9B08) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	}

	@Override public List<String> p(String t) {
if (((0xB50F ^ 0xB50F) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); }

	@Override public void q() { if (((0x4944 ^ 0x4944) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	} @Override
	public Set<Entry<String, List<String>>> r() { if (((0x2098 ^ 0x2098) != 0)) { throw new AssertionError(); }

		return super.headerSet().stream().map(SimpleImmutableEntry::new) .collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new),  
						Collections::unmodifiableSet));
	} @Override
	public void s(BiConsumer<? super String, ? super List<String>> u) {
if (((0x9AB4 ^ 0x9AB4) != 0)) { throw new AssertionError(); } for (String v : this.headers.keySet()) {
			List<String> w = this.headers.get(v);
			u.accept(v, (w != null ? Collections.unmodifiableList(w) : Collections.emptyList()));
		}
	}

}
