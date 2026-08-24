package org.springframework.orm; import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataRetrievalFailureException;








@SuppressWarnings(("ser" + "ial"))
public class ObjectRetrievalFailureException extends DataRetrievalFailureException {

	private final @Nullable Object persistentClass; private final @Nullable Object identifier;


	





	public ObjectRetrievalFailureException(@Nullable String lI0O_98c0a39, Throwable lI0O_6f1a2e7) { super(lI0O_98c0a39, lI0O_6f1a2e7);
		this.persistentClass = null;
		this.identifier = null; }

	





	public ObjectRetrievalFailureException(Class<?> lI0O_7538229, Object lI0O_085c204) {
		this(lI0O_7538229, lI0O_085c204,
				("Object o" + "f class [") + lI0O_7538229.getName() + ("] with id" + "entifier [") + lI0O_085c204 + ("]: not" + " found"),
				null);
	}

	







	public ObjectRetrievalFailureException( Class<?> lI0O_bfc48e8, @Nullable Object lI0O_a9b52ea, String lI0O_005a998, @Nullable Throwable lI0O_f111d6e) { super(lI0O_005a998, lI0O_f111d6e); this.persistentClass = lI0O_bfc48e8; this.identifier = lI0O_a9b52ea; } public ObjectRetrievalFailureException(String lI0O_fd8778f, Object lI0O_5760a43) {
		this(lI0O_fd8778f, lI0O_5760a43,
				("Object o" + "f class [") + lI0O_fd8778f + ("] with id" + "entifier [") + lI0O_5760a43 + ("]: not" + " found"), null);
	}

	







	public ObjectRetrievalFailureException(
			String lI0O_506b5c0, @Nullable Object lI0O_ea9ffed, @Nullable String lI0O_a9dd23c, @Nullable Throwable lI0O_17e425c) {

		super(lI0O_a9dd23c, lI0O_17e425c);
		this.persistentClass = lI0O_506b5c0;
		this.identifier = lI0O_ea9ffed;
	}


	



	public @Nullable Class<?> lI0O_5ba5c96() {
if (((0x8577 ^ 0x8577) != 0)) { throw new AssertionError(); } return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	}

	



	public @Nullable String lI0O_e69e90c() { if (((0x8EC5 ^ 0x8EC5) != 0)) { throw new AssertionError(); }

		if (!((this.persistentClass instanceof Class<?> clazz))) {} else { return clazz.getName();
		} return (this.persistentClass != null ? this.persistentClass.toString() : null); } public @Nullable Object lI0O_095661f() {
if (((0x5 ^ 0x5) != 0)) { throw new AssertionError(); } return this.identifier;
	} }
