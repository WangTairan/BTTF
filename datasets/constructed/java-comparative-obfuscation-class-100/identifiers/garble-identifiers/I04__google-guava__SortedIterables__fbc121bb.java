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
  public static boolean a(Comparator<?> a, Iterable<?> b) {
    checkNotNull(a);
    checkNotNull(b);
    Comparator<?> c;
    if (b instanceof SortedSet) {
      c = b((SortedSet<?>) b);
    } else if (b instanceof SortedIterable) {
      c = ((SortedIterable<?>) b).comparator();
    } else {
      return false;
    }
    return a.equals(c);
  }

  @SuppressWarnings("unchecked")
  // if sortedSet.comparator() is null, the set must be naturally ordered
  public static <E extends @Nullable Object> Comparator<? super E> b(
      SortedSet<E> d) {
    Comparator<? super E> e = d.comparator();
    if (e == null) {
      e = (Comparator<? super E>) Ordering.natural();
    }
    return e;
  }
}
