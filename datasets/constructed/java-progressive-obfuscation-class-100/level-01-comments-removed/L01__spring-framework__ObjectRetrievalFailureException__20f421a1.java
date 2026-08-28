package org.springframework.orm;
import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataRetrievalFailureException;








@SuppressWarnings("serial")
public class ObjectRetrievalFailureException extends DataRetrievalFailureException {

	private final @Nullable Object persistentClass;

	private final @Nullable Object identifier;


	





	public ObjectRetrievalFailureException(@Nullable String msg, Throwable cause) {
		super(msg, cause);
		this.persistentClass = null;
		this.identifier = null;
	}

	





	public ObjectRetrievalFailureException(Class<?> persistentClass, Object identifier) {
		this(persistentClass, identifier,
				"Object of class [" + persistentClass.getName() + "] with identifier [" + identifier + "]: not found",
				null);
	}

	







	public ObjectRetrievalFailureException(
			Class<?> persistentClass, @Nullable Object identifier, String msg, @Nullable Throwable cause) {

		super(msg, cause);
		this.persistentClass = persistentClass;
		this.identifier = identifier;
	}

	





	public ObjectRetrievalFailureException(String persistentClassName, Object identifier) {
		this(persistentClassName, identifier,
				"Object of class [" + persistentClassName + "] with identifier [" + identifier + "]: not found",
				null);
	}

	







	public ObjectRetrievalFailureException(
			String persistentClassName, @Nullable Object identifier, @Nullable String msg, @Nullable Throwable cause) {

		super(msg, cause);
		this.persistentClass = persistentClassName;
		this.identifier = identifier;
	}


	



	public @Nullable Class<?> getPersistentClass() {
		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	}

	



	public @Nullable String getPersistentClassName() {
		if (this.persistentClass instanceof Class<?> clazz) {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null);
	}

	


	public @Nullable Object getIdentifier() {
		return this.identifier;
	}

}
