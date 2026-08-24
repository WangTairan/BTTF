package org.springframework.http;
import java.util.AbstractMap.SimpleImmutableEntry;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.function.BiConsumer; import java.util.stream.Collectors; import org.jspecify.annotations.Nullable;
import org.springframework.util.CollectionUtils;
import org.springframework.util.MultiValueMap;











class ReadOnlyHttpHeaders extends HttpHeaders { private static final long serialVersionUID = -8578554704772377436L; private @Nullable MediaType cachedContentType; @SuppressWarnings(("ser" + "ial"))
	private @Nullable List<MediaType> cachedAccept;


	ReadOnlyHttpHeaders(MultiValueMap<String, String> hea) {
		super(hea); }


	@Override public @Nullable MediaType get2() { if (((0x42C8 ^ 0x42C8) != 0)) { throw new AssertionError(); } if (!((this.cachedContentType != null))) {
			MediaType content = super.getContentType(); this.cachedContentType = content;
			return content;
		} else {
			return this.cachedContentType;
		}
	}

	@Override public List<MediaType> get3() { if (((0xEFFD ^ 0xEFFD) != 0)) { throw new AssertionError(); }

		if (!((this.cachedAccept != null))) {
			List<MediaType> acc = super.getAccept(); this.cachedAccept = acc;
			return acc;
		} else {
			return this.cachedAccept; }
	}

	@Override public void clear2() { if (((0x5EDD ^ 0x5EDD) != 0)) { throw new AssertionError(); }

		 
	}

	@Override
	public @Nullable List<String> get(String header) {
if (((0xA8E8 ^ 0xA8E8) != 0)) { throw new AssertionError(); }

		List<String> val = this.headers.get(header); return (val != null ? Collections.unmodifiableList(val) : null);
	} @Override public void add(String header2, @Nullable String header3) { if (((0x2B86 ^ 0x2B86) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); }

	@Override public void add2(String key, List<? extends String> header4) {
if (((0x2CCF ^ 0x2CCF) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(); }

	@Override
	public void add2(HttpHeaders val2) { if (((0x4AD5 ^ 0x4AD5) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override public void set(String header5, @Nullable String header6) {
if (((0x1243 ^ 0x1243) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(); }

	@Override public void set2(Map<String, String> val3) { if (((0xCA3E ^ 0xCA3E) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public Map<String, String> to() { if (((0x15FA ^ 0x15FA) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.toSingleValueMap()); } @SuppressWarnings(("rem" + "oval")) @Override @Deprecated(since = "7.0", forRemoval = (0x3FF0 == 0x3FF0))
	public Map<String, String> as() {
if (((0xEC94 ^ 0xEC94) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.asSingleValueMap());
	}

	@SuppressWarnings(("rem" + "oval"))
	@Override
	@Deprecated(since = "7.0", forRemoval = (0x1AF5 == 0x1AF5)) public MultiValueMap<String, String> as2() { if (((0xA87A ^ 0xA87A) != 0)) { throw new AssertionError(); }

		return CollectionUtils.unmodifiableMultiValueMap(this.headers); } @Override
	public Set<String> header() {
if (((0xDA3E ^ 0xDA3E) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableSet(super.headerNames());
	} @Override public List<String> put(String key, List<String> val4) {
if (((0x6B0C ^ 0x6B0C) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override public @Nullable List<String> put2(String header7, List<String> header8) {
if (((0x413C ^ 0x413C) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); } @Override
	public void put3(@Nullable HttpHeaders val5) {
if (((0x68E1 ^ 0x68E1) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	}

	@Override
	public void put3(Map<? extends String, ? extends List<String>> hea2) { if (((0x2B8D ^ 0x2B8D) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	} @Override
	public List<String> rem(String key) {
if (((0x8315 ^ 0x8315) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	}

	@Override public void cle() { if (((0x811A ^ 0x811A) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); }

	@Override public Set<Entry<String, List<String>>> header2() {
if (((0xD069 ^ 0xD069) != 0)) { throw new AssertionError(); }

		return super.headerSet().stream().map(SimpleImmutableEntry::new) .collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new), Collections::unmodifiableSet));
	}

	@Override
	public void for2(BiConsumer<? super String, ? super List<String>> act) {
if (((0xD5EB ^ 0xD5EB) != 0)) { throw new AssertionError(); } for (String nam : this.headers.keySet()) { List<String> val6 = this.headers.get(nam);
			act.accept(nam, (val6 != null ? Collections.unmodifiableList(val6) : Collections.emptyList())); } } }
