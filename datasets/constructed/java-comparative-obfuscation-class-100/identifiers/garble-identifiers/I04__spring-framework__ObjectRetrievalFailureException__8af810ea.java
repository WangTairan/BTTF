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
	public ObjectRetrievalFailureException(@Nullable String a, Throwable b) {
		super(a, b);
		this.persistentClass = null;
		this.identifier = null;
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the default "not found" message.
	 * @param persistentClass the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 */
	public ObjectRetrievalFailureException(Class<?> c, Object d) {
		this(c, d,
				"Object of class [" + c.getName() + "] with identifier [" + d + "]: not found",
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
			Class<?> e, @Nullable Object f, String g, @Nullable Throwable h) {

		super(g, h);
		this.persistentClass = e;
		this.identifier = f;
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the default "not found" message.
	 * @param persistentClassName the name of the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 */
	public ObjectRetrievalFailureException(String i, Object j) {
		this(i, j,
				"Object of class [" + i + "] with identifier [" + j + "]: not found",
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
			String k, @Nullable Object l, @Nullable String m, @Nullable Throwable n) {

		super(m, n);
		this.persistentClass = k;
		this.identifier = l;
	}


	/**
	 * Return the persistent class of the object that was not found.
	 * If no Class was specified, this method returns null.
	 */
	public @Nullable Class<?> a() {
		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	}

	/**
	 * Return the name of the persistent class of the object that was not found.
	 * Will work for both Class objects and String names.
	 */
	public @Nullable String b() {
		if (this.persistentClass instanceof Class<?> clazz) {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null);
	}

	/**
	 * Return the identifier of the object that was not found.
	 */
	public @Nullable Object c() {
		return this.identifier;
	}

}
