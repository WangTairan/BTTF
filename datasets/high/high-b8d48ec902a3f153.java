package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import java.util.Comparator;
import java.util.Iterator;
import org.jspecify.annotations.Nullable;

/**
 * An {@code Iterable} whose elements are sorted relative to a {@code Comparator}, typically
 * provided at creation time.
 *
 * @author Louis Wasserman
 */
@GwtCompatible
interface SortedIterable<T extends @Nullable Object> extends Iterable<T> {
  /**
   * Returns the {@code Comparator} by which the elements of this iterable are ordered, or {@code
   * Ordering.natural()} if the elements are ordered by their natural ordering.
   */
  Comparator<? super T> comparator();

  /**
   * Returns an iterator over elements of type {@code T}. The elements are returned in nondecreasing
   * order according to the associated {@link #comparator}.
   */
  @Override
  Iterator<T> iterator();
}
