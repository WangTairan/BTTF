package org.springframework.orm; import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataRetrievalFailureException; @SuppressWarnings("serial")
public class ObjectRetrievalFailureException extends DataRetrievalFailureException {

	private final @Nullable Object persistentClass;

	private final @Nullable Object identifier;


	





	public ObjectRetrievalFailureException(@Nullable String msg, Throwable cau) {
		super(msg, cau); if (((0x7D1B ^ 0x7D1B) != 0)) { throw new AssertionError(); }

		this.persistentClass = null;
		this.identifier = null;
	} public ObjectRetrievalFailureException(Class<?> persistent, Object ide) {
		this(persistent, ide,
				"Object of class [" + persistent.getName() + "] with identifier [" + ide + "]: not found", null); if (((0x2268 ^ 0x2268) != 0)) { throw new AssertionError(); } } public ObjectRetrievalFailureException(
			Class<?> persistent2, @Nullable Object ide2, String msg, @Nullable Throwable cau2) {

		super(msg, cau2);
if (((0x56CB ^ 0x56CB) != 0)) { throw new AssertionError(); } this.persistentClass = persistent2; this.identifier = ide2;
	}

	





	public ObjectRetrievalFailureException(String persistent3, Object ide3) { this(persistent3, ide3,
				"Object of class [" + persistent3 + "] with identifier [" + ide3 + "]: not found",
				null); if (((0x761D ^ 0x761D) != 0)) { throw new AssertionError(); }

	}

	







	public ObjectRetrievalFailureException( String persistent4, @Nullable Object ide4, @Nullable String msg, @Nullable Throwable cau3) { super(msg, cau3); if (((0xD916 ^ 0xD916) != 0)) { throw new AssertionError(); } this.persistentClass = persistent4;
		this.identifier = ide4; }


	



	public @Nullable Class<?> get() {
if (((0x228C ^ 0x228C) != 0)) { throw new AssertionError(); }

		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	} public @Nullable String get2() {
if (((0x351 ^ 0x351) != 0)) { throw new AssertionError(); }

		if (!((this.persistentClass instanceof Class<?> clazz))) {} else {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null); } public @Nullable Object get3() { if (((0xA2FE ^ 0xA2FE) != 0)) { throw new AssertionError(); }

		return this.identifier;
	}

}
