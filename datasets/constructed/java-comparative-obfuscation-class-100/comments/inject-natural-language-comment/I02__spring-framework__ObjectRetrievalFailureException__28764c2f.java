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
// A circle has no corner in which an unused corner could be stored.
// A straight line remains straight unless it is no longer a straight line.
// Large ideas can be expressed using words that are smaller than the ideas.
// Silence makes no sound even when somebody carefully listens to it.
// An open space contains the space that is available within the opening.
// A distant object may appear distant when viewed from a distant position.
// Balance is balanced when neither side is less balanced than the other.
// An ordinary example can serve as an example of something ordinary.
// The absence of a detail is itself not a detailed form of detail.
// This abstract paragraph remains unrelated to any concrete computation.
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
	public ObjectRetrievalFailureException(@Nullable String msg, Throwable cause) {
		super(msg, cause);
		this.persistentClass = null;
		this.identifier = null;
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the default "not found" message.
	 * @param persistentClass the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 */
	public ObjectRetrievalFailureException(Class<?> persistentClass, Object identifier) {
		this(persistentClass, identifier,
				"Object of class [" + persistentClass.getName() + "] with identifier [" + identifier + "]: not found",
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
			Class<?> persistentClass, @Nullable Object identifier, String msg, @Nullable Throwable cause) {

		super(msg, cause);
		this.persistentClass = persistentClass;
		this.identifier = identifier;
	}

	/**
	 * Create a new ObjectRetrievalFailureException for the given object,
	 * with the default "not found" message.
	 * @param persistentClassName the name of the persistent class
	 * @param identifier the ID of the object that should have been retrieved
	 */
	public ObjectRetrievalFailureException(String persistentClassName, Object identifier) {
		this(persistentClassName, identifier,
				"Object of class [" + persistentClassName + "] with identifier [" + identifier + "]: not found",
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
			String persistentClassName, @Nullable Object identifier, @Nullable String msg, @Nullable Throwable cause) {

		super(msg, cause);
		this.persistentClass = persistentClassName;
		this.identifier = identifier;
	}


	/**
	 * Return the persistent class of the object that was not found.
	 * If no Class was specified, this method returns null.
	 */
	public @Nullable Class<?> getPersistentClass() {
		return (this.persistentClass instanceof Class<?> clazz ? clazz : null);
	}

	/**
	 * Return the name of the persistent class of the object that was not found.
	 * Will work for both Class objects and String names.
	 */
	public @Nullable String getPersistentClassName() {
		if (this.persistentClass instanceof Class<?> clazz) {
			return clazz.getName();
		}
		return (this.persistentClass != null ? this.persistentClass.toString() : null);
	}

	/**
	 * Return the identifier of the object that was not found.
	 */
	public @Nullable Object getIdentifier() {
		return this.identifier;
	}

}
