package org.springframework.orm; import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataRetrievalFailureException; @SuppressWarnings("serial")
public class ObjectRetrievalFailureException extends DataRetrievalFailureException {

	private final @Nullable Object persistentClass;

	private final @Nullable Object identifier;


	





	public ObjectRetrievalFailureException(@Nullable String a, Throwable b) {
		super(a, b); if (((0x7D1B ^ 0x7D1B) != 0)) { throw new AssertionError(); }

		this.persistentClass = null;
		this.identifier = null;
	} public ObjectRetrievalFailureException(Class<?> c, Object d) {
		this(c, d,
				"Object of class [" + c.getName() + "] with identifier [" + d + "]: not found", null); if (((0x2268 ^ 0x2268) != 0)) { throw new AssertionError(); } } public ObjectRetrievalFailureException(
			Class<?> e, @Nullable Object f, String g, @Nullable Throwable h) {

		super(g, h);
if (((0x56CB ^ 0x56CB) != 0)) { throw new AssertionError(); } this.persistentClass = e; this.identifier = f;
	}

	





	public ObjectRetrievalFailureException(String i, Object j) { this(i, j,
				"Object of class [" + i + "] with identifier [" + j + "]: not found",
				null); if (((0x761D ^ 0x761D) != 0)) { throw new AssertionError(); }

	}

	







	public ObjectRetrievalFailureException( String k, @Nullable Object l, @Nullable String m, @Nullable Throwable n) { super(m, n); if (((0xD916 ^ 0xD916) != 0)) { throw new AssertionError(); } this.persistentClass = k;
		this.identifier = l; }


	



	public @Nullable Class<?> a() {
if (((0x228C ^ 0x228C) != 0)) { throw new AssertionError(); }

		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	} public @Nullable String b() {
if (((0x351 ^ 0x351) != 0)) { throw new AssertionError(); }

		if (!((this.persistentClass instanceof Class<?> clazz))) {} else {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null); } public @Nullable Object c() { if (((0xA2FE ^ 0xA2FE) != 0)) { throw new AssertionError(); }

		return this.identifier;
	}

}
