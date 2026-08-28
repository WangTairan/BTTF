package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import com.google.errorprone.annotations.DoNotMock;
import java.util.Iterator;
import java.util.NoSuchElementException;
import org.jspecify.annotations.Nullable;

/**
 * An iterator that supports a one-element lookahead while iterating.
 *
 * <p>See the Guava User Guide article on <a href=
 * "https://github.com/google/guava/wiki/CollectionHelpersExplained#peekingiterator">{@code
 * PeekingIterator}</a>.
 *
 * @author Mick Killianey
 * @since 2.0
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
@DoNotMock("Use Iterators.peekingIterator")
@GwtCompatible
public interface PeekingIterator<E extends @Nullable Object> extends Iterator<E> {
  /**
   * Returns the next element in the iteration, without advancing the iteration.
   *
   * <p>Calls to {@code peek()} should not change the state of the iteration, except that it
   * <i>may</i> prevent removal of the most recent element via {@link #remove()}.
   *
   * @throws NoSuchElementException if the iteration has no more elements according to {@link
   *     #hasNext()}
   */
  @ParametricNullness
  E peek();

  /**
   * {@inheritDoc}
   *
   * <p>The objects returned by consecutive calls to {@link #peek()} then {@link #next()} are
   * guaranteed to be equal to each other.
   */
  @CanIgnoreReturnValue
  @Override
  @ParametricNullness
  E next();

  /**
   * {@inheritDoc}
   *
   * <p>Implementations may or may not support removal when a call to {@link #peek()} has occurred
   * since the most recent call to {@link #next()}.
   *
   * @throws IllegalStateException if there has been a call to {@link #peek()} since the most recent
   *     call to {@link #next()} and this implementation does not support this sequence of calls
   *     (optional)
   */
  @Override
  void remove();
}
