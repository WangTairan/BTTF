package com.google.common.base;
import static com.google.common.base.NullnessCasts.uncheckedCastNullableTToT;
import static com.google.common.base.Preconditions.checkState;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Iterator;
import java.util.NoSuchElementException;
import org.jspecify.annotations.Nullable;

/**
 * Note this class is a copy of {@link com.google.common.collect.AbstractIterator} (for dependency
 * reasons).
 */
@GwtCompatible
abstract class AbstractIterator<T extends @Nullable Object> implements Iterator<T> {
  private State state = State.NOT_READY;

  protected AbstractIterator() {}

  private enum State {
    READY,
    NOT_READY,
    DONE,
    FAILED,
  }

  private @Nullable T next;

  protected abstract @Nullable T computeNext();

  @CanIgnoreReturnValue
  protected final @Nullable T endOfData() {
    state = State.DONE;
    return null;
  }

  @Override
  public final boolean hasNext() {
    checkState(state != State.FAILED);
    switch (state) {
      case DONE:
        return false;
      case READY:
        return true;
      default:
    }
    return tryToComputeNext();
  }

  private boolean tryToComputeNext() {
    state = State.FAILED; // temporary pessimism
    next = computeNext();
    if (state != State.DONE) {
      state = State.READY;
      return true;
    }
    return false;
  }

  @Override
  @ParametricNullness
  public final T next() {
    if (!hasNext()) {
      throw new NoSuchElementException();
    }
    state = State.NOT_READY;
    // Safe because hasNext() ensures that tryToComputeNext() has put a T into `next`.
    T result = uncheckedCastNullableTToT(next);
    next = null;
    return result;
  }

  @Override
  public final void remove() {
    throw new UnsupportedOperationException();
  }
}
