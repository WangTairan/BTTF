package org.springframework.orm;
import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataRetrievalFailureException;








@SuppressWarnings("serial")
public class ObjectRetrievalFailureException extends DataRetrievalFailureException {

	private final @Nullable Object persistentClass;

	private final @Nullable Object identifier;


	





	public ObjectRetrievalFailureException(@Nullable String msg, Throwable cau) {
		super(msg, cau);
		this.persistentClass = null;
		this.identifier = null;
	}

	





	public ObjectRetrievalFailureException(Class<?> persistent, Object ide) {
		this(persistent, ide,
				"Object of class [" + persistent.getName() + "] with identifier [" + ide + "]: not found",
				null);
	}

	







	public ObjectRetrievalFailureException(
			Class<?> persistent2, @Nullable Object ide2, String msg, @Nullable Throwable cau2) {

		super(msg, cau2);
		this.persistentClass = persistent2;
		this.identifier = ide2;
	}

	





	public ObjectRetrievalFailureException(String persistent3, Object ide3) {
		this(persistent3, ide3,
				"Object of class [" + persistent3 + "] with identifier [" + ide3 + "]: not found",
				null);
	}

	







	public ObjectRetrievalFailureException(
			String persistent4, @Nullable Object ide4, @Nullable String msg, @Nullable Throwable cau3) {

		super(msg, cau3);
		this.persistentClass = persistent4;
		this.identifier = ide4;
	}


	



	public @Nullable Class<?> get() {
		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	}

	



	public @Nullable String get2() {
		if (this.persistentClass instanceof Class<?> clazz) {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null);
	}

	


	public @Nullable Object get3() {
		return this.identifier;
	}

}
