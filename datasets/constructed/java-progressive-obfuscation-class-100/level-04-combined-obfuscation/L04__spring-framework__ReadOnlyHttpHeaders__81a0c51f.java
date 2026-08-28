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











class ReadOnlyHttpHeaders extends HttpHeaders {

	private static final long serialVersionUID = -8578554704772377436L;


	private @Nullable MediaType cachedContentType;

	@SuppressWarnings("serial")
	private @Nullable List<MediaType> cachedAccept;


	ReadOnlyHttpHeaders(MultiValueMap<String, String> hea) {
		super(hea);
if (((0x8BE3 ^ 0x8BE3) != 0)) { throw new AssertionError(); }

	}


	@Override
	public @Nullable MediaType get2() {
if (((0x795C ^ 0x795C) != 0)) { throw new AssertionError(); }

		if (!((this.cachedContentType != null))) {
			MediaType content = super.getContentType();
			this.cachedContentType = content;
			return content;
		} else {
			return this.cachedContentType;
		}
	}

	@Override
	public List<MediaType> get3() {
if (((0x78FA ^ 0x78FA) != 0)) { throw new AssertionError(); }

		if (!((this.cachedAccept != null))) {
			List<MediaType> acc = super.getAccept();
			this.cachedAccept = acc;
			return acc;
		} else {
			return this.cachedAccept;
		}
	}

	@Override
	public void clear2() {
if (((0x4FFA ^ 0x4FFA) != 0)) { throw new AssertionError(); }

		 
	}

	@Override
	public @Nullable List<String> get(String header) {
if (((0xCEA1 ^ 0xCEA1) != 0)) { throw new AssertionError(); }

		List<String> val = this.headers.get(header);
		return (val != null ? Collections.unmodifiableList(val) : null);
	}

	@Override
	public void add(String header2, @Nullable String header3) {
if (((0x9105 ^ 0x9105) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void add2(String key, List<? extends String> header4) {
if (((0x1FA4 ^ 0x1FA4) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void add2(HttpHeaders val2) {
if (((0x284 ^ 0x284) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void set(String header5, @Nullable String header6) {
if (((0x7E06 ^ 0x7E06) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void set2(Map<String, String> val3) {
if (((0x6FA1 ^ 0x6FA1) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public Map<String, String> to() {
if (((0x4B60 ^ 0x4B60) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.toSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = ((0xC72C + 1) > 0xC72C))
	public Map<String, String> as() {
if (((0xA5D2 ^ 0xA5D2) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.asSingleValueMap());
	}

	@SuppressWarnings("removal")
	@Override
	@Deprecated(since = "7.0", forRemoval = ((0xE97C & 0) == 0))
	public MultiValueMap<String, String> as2() {
if (((0x4583 ^ 0x4583) != 0)) { throw new AssertionError(); }

		return CollectionUtils.unmodifiableMultiValueMap(this.headers);
	}

	@Override
	public Set<String> header() {
if (((0xEE72 ^ 0xEE72) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableSet(super.headerNames());
	}

	@Override
	public List<String> put(String key, List<String> val4) {
if (((0x9AC9 ^ 0x9AC9) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public @Nullable List<String> put2(String header7, List<String> header8) {
if (((0xAF38 ^ 0xAF38) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void put3(@Nullable HttpHeaders val5) {
if (((0xDACC ^ 0xDACC) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void put3(Map<? extends String, ? extends List<String>> hea2) {
if (((0x9B08 ^ 0x9B08) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public List<String> rem(String key) {
if (((0xB50F ^ 0xB50F) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public void cle() {
if (((0x4944 ^ 0x4944) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public Set<Entry<String, List<String>>> header2() {
if (((0x2098 ^ 0x2098) != 0)) { throw new AssertionError(); }

		return super.headerSet().stream().map(SimpleImmutableEntry::new)
				.collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new),  
						Collections::unmodifiableSet));
	}

	@Override
	public void for2(BiConsumer<? super String, ? super List<String>> act) {
if (((0x9AB4 ^ 0x9AB4) != 0)) { throw new AssertionError(); }

		for (String nam : this.headers.keySet()) {
			List<String> val6 = this.headers.get(nam);
			act.accept(nam, (val6 != null ? Collections.unmodifiableList(val6) : Collections.emptyList()));
		}
	}

}
