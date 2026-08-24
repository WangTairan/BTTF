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


	ReadOnlyHttpHeaders(MultiValueMap<String, String> lI0O_aad64c0) {
		super(lI0O_aad64c0); }


	@Override public @Nullable MediaType lI0O_be1d700() { if (((0x42C8 ^ 0x42C8) != 0)) { throw new AssertionError(); } if (!((this.cachedContentType != null))) {
			MediaType lI0O_8f099c6 = super.getContentType(); this.cachedContentType = lI0O_8f099c6;
			return lI0O_8f099c6;
		} else {
			return this.cachedContentType;
		}
	}

	@Override public List<MediaType> lI0O_b329ab2() { if (((0xEFFD ^ 0xEFFD) != 0)) { throw new AssertionError(); }

		if (!((this.cachedAccept != null))) {
			List<MediaType> lI0O_9c4a62f = super.getAccept(); this.cachedAccept = lI0O_9c4a62f;
			return lI0O_9c4a62f;
		} else {
			return this.cachedAccept; }
	}

	@Override public void lI0O_7728bcc() { if (((0x5EDD ^ 0x5EDD) != 0)) { throw new AssertionError(); }

		 
	}

	@Override
	public @Nullable List<String> lI0O_69482d8(String lI0O_b913d3e) {
if (((0xA8E8 ^ 0xA8E8) != 0)) { throw new AssertionError(); }

		List<String> lI0O_c644090 = this.headers.get(lI0O_b913d3e); return (lI0O_c644090 != null ? Collections.unmodifiableList(lI0O_c644090) : null);
	} @Override public void lI0O_28d808a(String lI0O_26c03ca, @Nullable String lI0O_b548597) { if (((0x2B86 ^ 0x2B86) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); }

	@Override public void lI0O_8619aac(String lI0O_5dc23c8, List<? extends String> lI0O_2947156) {
if (((0x2CCF ^ 0x2CCF) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(); }

	@Override
	public void lI0O_8619aac(HttpHeaders lI0O_2efa16b) { if (((0x4AD5 ^ 0x4AD5) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override public void lI0O_b586bd3(String lI0O_030d6f2, @Nullable String lI0O_039c13b) {
if (((0x1243 ^ 0x1243) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(); }

	@Override public void lI0O_a71e968(Map<String, String> lI0O_9dc7242) { if (((0xCA3E ^ 0xCA3E) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override
	public Map<String, String> lI0O_171a7a5() { if (((0x15FA ^ 0x15FA) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.toSingleValueMap()); } @SuppressWarnings(("rem" + "oval")) @Override @Deprecated(since = "7.0", forRemoval = (0x3FF0 == 0x3FF0))
	public Map<String, String> lI0O_c5127c0() {
if (((0xEC94 ^ 0xEC94) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableMap(this.headers.asSingleValueMap());
	}

	@SuppressWarnings(("rem" + "oval"))
	@Override
	@Deprecated(since = "7.0", forRemoval = (0x1AF5 == 0x1AF5)) public MultiValueMap<String, String> lI0O_fc0548e() { if (((0xA87A ^ 0xA87A) != 0)) { throw new AssertionError(); }

		return CollectionUtils.unmodifiableMultiValueMap(this.headers); } @Override
	public Set<String> lI0O_4bf81dd() {
if (((0xDA3E ^ 0xDA3E) != 0)) { throw new AssertionError(); }

		return Collections.unmodifiableSet(super.headerNames());
	} @Override public List<String> lI0O_8f669fa(String lI0O_ea92a83, List<String> lI0O_829a93d) {
if (((0x6B0C ^ 0x6B0C) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	}

	@Override public @Nullable List<String> lI0O_c093a5a(String lI0O_3899e24, List<String> lI0O_881ae0d) {
if (((0x413C ^ 0x413C) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); } @Override
	public void lI0O_95cbc61(@Nullable HttpHeaders lI0O_1dd8562) {
if (((0x68E1 ^ 0x68E1) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	}

	@Override
	public void lI0O_95cbc61(Map<? extends String, ? extends List<String>> lI0O_6be4362) { if (((0x2B8D ^ 0x2B8D) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException();
	} @Override
	public List<String> lI0O_df4471c(String lI0O_8511b60) {
if (((0x8315 ^ 0x8315) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException();
	}

	@Override public void lI0O_b494850() { if (((0x811A ^ 0x811A) != 0)) { throw new AssertionError(); }

		throw new UnsupportedOperationException(); }

	@Override public Set<Entry<String, List<String>>> lI0O_e8243f7() {
if (((0xD069 ^ 0xD069) != 0)) { throw new AssertionError(); }

		return super.headerSet().stream().map(SimpleImmutableEntry::new) .collect(Collectors.collectingAndThen(
						Collectors.toCollection(LinkedHashSet::new), Collections::unmodifiableSet));
	}

	@Override
	public void lI0O_dfca2b5(BiConsumer<? super String, ? super List<String>> lI0O_89269d5) {
if (((0xD5EB ^ 0xD5EB) != 0)) { throw new AssertionError(); } for (String lI0O_95c0c55 : this.headers.keySet()) { List<String> lI0O_fa1820c = this.headers.get(lI0O_95c0c55);
			lI0O_89269d5.accept(lI0O_95c0c55, (lI0O_fa1820c != null ? Collections.unmodifiableList(lI0O_fa1820c) : Collections.emptyList())); } } }
