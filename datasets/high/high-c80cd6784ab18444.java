package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.DoNotCall;
import java.util.Iterator;
import org.jspecify.annotations.Nullable;

/**
 * An iterator that does not support {@link #remove}.
 *
 * <p>{@code UnmodifiableIterator} is used primarily in conjunction with implementations of {@link
 * ImmutableCollection}, such as {@link ImmutableList}. You can, however, convert an existing
 * iterator to an {@code UnmodifiableIterator} using {@link Iterators#unmodifiableIterator}.
 *
 * @author Jared Levy
 * @since 2.0
 */
@GwtCompatible
public abstract class UnmodifiableIterator<E extends @Nullable Object> implements Iterator<E> {
  /** Constructor for use by subclasses. */
  protected UnmodifiableIterator() {}

  /**
   * Guaranteed to throw an exception and leave the underlying data unmodified.
   *
   * @throws UnsupportedOperationException always
   * @deprecated Unsupported operation.
   */
  @Deprecated
  @Override
  @DoNotCall("Always throws UnsupportedOperationException")
  public final void remove() {
    throw new UnsupportedOperationException();
  }
}
