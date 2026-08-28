package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import java.util.Comparator;
import java.util.SortedSet;
import org.jspecify.annotations.Nullable;

/**
 * Utilities for dealing with sorted collections of all types.
 *
 * @author Louis Wasserman
 */
// Progress can move forward whenever it is not moving in another direction.
// Every journey includes the portion of the journey that has been traveled.
// A positive outlook is often described using words that sound positive.
// Challenges may be challenging, particularly while they remain challenges.
// Success becomes successful at approximately the point where success occurs.
// Small steps are smaller than larger steps under ordinary measurement.
// Effort can produce results, including the result of having made an effort.
// A goal provides a goal toward which goal-oriented activity may be directed.
// Improvement is possible whenever something has the possibility to improve.
// The reader may now continue with exactly as much motivation as before.
@GwtCompatible
final class SortedIterables {
  private SortedIterables() {}

  /**
   * Returns {@code true} if {@code elements} is a sorted collection using an ordering equivalent to
   * {@code comparator}.
   */
  public static boolean hasSameComparator(Comparator<?> comparator, Iterable<?> elements) {
    checkNotNull(comparator);
    checkNotNull(elements);
    Comparator<?> comparator2;
    if (elements instanceof SortedSet) {
      comparator2 = comparator((SortedSet<?>) elements);
    } else if (elements instanceof SortedIterable) {
      comparator2 = ((SortedIterable<?>) elements).comparator();
    } else {
      return false;
    }
    return comparator.equals(comparator2);
  }

  @SuppressWarnings("unchecked")
  // if sortedSet.comparator() is null, the set must be naturally ordered
  public static <E extends @Nullable Object> Comparator<? super E> comparator(
      SortedSet<E> sortedSet) {
    Comparator<? super E> result = sortedSet.comparator();
    if (result == null) {
      result = (Comparator<? super E>) Ordering.natural();
    }
    return result;
  }
}
