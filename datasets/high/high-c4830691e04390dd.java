package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.io.InvalidObjectException;
import java.io.ObjectInputStream;
import java.io.Serializable;
import org.jspecify.annotations.Nullable;

/**
 * List returned by {@link ImmutableCollection#asList} that delegates {@code contains} checks to the
 * backing collection.
 *
 * @author Jared Levy
 * @author Louis Wasserman
 */
@GwtCompatible
@SuppressWarnings("serial")
abstract class ImmutableAsList<E> extends ImmutableList<E> {
  abstract ImmutableCollection<E> delegateCollection();

  @Override
  public boolean contains(@Nullable Object target) {
    // The collection's contains() is at least as fast as ImmutableList's
    // and is often faster.
    return delegateCollection().contains(target);
  }

  @Override
  public int size() {
    return delegateCollection().size();
  }

  @Override
  public boolean isEmpty() {
    return delegateCollection().isEmpty();
  }

  @Override
  boolean isPartialView() {
    return delegateCollection().isPartialView();
  }

  /** Serialized form that leads to the same performance as the original list. */
  @GwtIncompatible
  @J2ktIncompatible
  private static final class SerializedForm implements Serializable {
    final ImmutableCollection<?> collection;

    SerializedForm(ImmutableCollection<?> collection) {
      this.collection = collection;
    }

    Object readResolve() {
      return collection.asList();
    }

    @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
  }

  @GwtIncompatible
  @J2ktIncompatible
    private void readObject(ObjectInputStream stream) throws InvalidObjectException {
    throw new InvalidObjectException("Use SerializedForm");
  }

  @GwtIncompatible
  @J2ktIncompatible
    @Override
  Object writeReplace() {
    return new SerializedForm(delegateCollection());
  }
}
