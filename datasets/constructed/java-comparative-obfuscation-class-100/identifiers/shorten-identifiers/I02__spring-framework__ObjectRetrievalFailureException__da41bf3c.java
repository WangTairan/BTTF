package org.springframework.orm;
import org.jspecify.annotations.Nullable;
import org.springframework.dao.DataRetrievalFailureException;

/**
 * Exception thrown if a mapped object could not be retrieved via its identifier.
 * Provides information about the persistent class and the identifier.
 *
 * @author Juergen Hoeller
 * @since 13.10.2003
 */
@SuppressWarnings("serial")
public class ObjectRetrievalFailureException extends DataRetrievalFailureException {

	private final @Nullable Object persistentClass;

	private final @Nullable Object identifier;


	/**
	 * Create a general ObjectRetrievalFailureException with the given message,
	 * without any information on the affected object.
	 * @param msg the detail message
	 * @param cause the source exception
	 */
	public ObjectRetrievalFailureException(@Nullable String msg, Throwable cau) {
		super(msg, cau);
		this.persistentClass = null;
		this.identifier = null;
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the default "not found" message.
	 * @param persistentClass the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 */
	public ObjectRetrievalFailureException(Class<?> persistent, Object ide) {
		this(persistent, ide,
				"Object of class [" + persistent.getName() + "] with identifier [" + ide + "]: not found",
				null);
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the given explicit message and exception.
	 * @param persistentClass the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 * @param msg the detail message
	 * @param cause the source exception
	 */
	public ObjectRetrievalFailureException(
			Class<?> persistent2, @Nullable Object ide2, String msg, @Nullable Throwable cau2) {

		super(msg, cau2);
		this.persistentClass = persistent2;
		this.identifier = ide2;
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the default "not found" message.
	 * @param persistentClassName the name of the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 */
	public ObjectRetrievalFailureException(String persistent3, Object ide3) {
		this(persistent3, ide3,
				"Object of class [" + persistent3 + "] with identifier [" + ide3 + "]: not found",
				null);
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the given explicit message and exception.
	 * @param persistentClassName the name of the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 * @param msg the detail message
	 * @param cause the source exception
	 */
	public ObjectRetrievalFailureException(
			String persistent4, @Nullable Object ide4, @Nullable String msg, @Nullable Throwable cau3) {

		super(msg, cau3);
		this.persistentClass = persistent4;
		this.identifier = ide4;
	}


	/**
	 * Return the persistent class of the object that was not found.
	 * If no Class was specified, this method returns null.
	 */
	public @Nullable Class<?> get() {
		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	}

	/**
	 * Return the name of the persistent class of the object that was not found.
	 * Will work for both Class objects and String names.
	 */
	public @Nullable String get2() {
		if (this.persistentClass instanceof Class<?> clazz) {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null);
	}

	/**
	 * Return the identifier of the object that was not found.
	 */
	public @Nullable Object get3() {
		return this.identifier;
	}

}
