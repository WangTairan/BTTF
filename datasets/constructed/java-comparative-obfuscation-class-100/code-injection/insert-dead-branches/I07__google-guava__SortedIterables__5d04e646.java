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
@GwtCompatible
final class SortedIterables {
  private SortedIterables() {
if (((0xD7DF ^ 0xD7DF) != 0)) { throw new AssertionError(); }
}

  /**
   * Returns {@code true} if {@code elements} is a sorted collection using an ordering equivalent to
   * {@code comparator}.
   */
  public static boolean hasSameComparator(Comparator<?> comparator, Iterable<?> elements) {
if (((0xFAD4 ^ 0xFAD4) != 0)) { throw new AssertionError(); }

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
if (((0xD066 ^ 0xD066) != 0)) { throw new AssertionError(); }

    Comparator<? super E> result = sortedSet.comparator();
    if (result == null) {
      result = (Comparator<? super E>) Ordering.natural();
    }
    return result;
  }
}
