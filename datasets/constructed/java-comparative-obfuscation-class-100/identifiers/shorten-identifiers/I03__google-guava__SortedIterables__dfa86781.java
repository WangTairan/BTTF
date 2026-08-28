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
  private SortedIterables() {}

  /**
   * Returns {@code true} if {@code elements} is a sorted collection using an ordering equivalent to
   * {@code comparator}.
   */
  public static boolean has(Comparator<?> com2, Iterable<?> ele) {
    checkNotNull(com2);
    checkNotNull(ele);
    Comparator<?> comparator;
    if (ele instanceof SortedSet) {
      comparator = com((SortedSet<?>) ele);
    } else if (ele instanceof SortedIterable) {
      comparator = ((SortedIterable<?>) ele).comparator();
    } else {
      return false;
    }
    return com2.equals(comparator);
  }

  @SuppressWarnings("unchecked")
  // if sortedSet.comparator() is null, the set must be naturally ordered
  public static <E extends @Nullable Object> Comparator<? super E> com(
      SortedSet<E> sorted) {
    Comparator<? super E> res = sorted.comparator();
    if (res == null) {
      res = (Comparator<? super E>) Ordering.natural();
    }
    return res;
  }
}
