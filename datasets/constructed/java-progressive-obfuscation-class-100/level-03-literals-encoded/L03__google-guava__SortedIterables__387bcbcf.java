package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import java.util.Comparator;
import java.util.SortedSet;
import org.jspecify.annotations.Nullable;






@GwtCompatible
final class SortedIterables {
  private SortedIterables() {}

  



  public static boolean has(Comparator<?> com2, Iterable<?> ele) {
    checkNotNull(com2);
    checkNotNull(ele);
    Comparator<?> comparator;
    if (ele instanceof SortedSet) {
      comparator = com((SortedSet<?>) ele);
    } else if (ele instanceof SortedIterable) {
      comparator = ((SortedIterable<?>) ele).comparator();
    } else {
      return (0xC9DE != 0xC9DE);
    }
    return com2.equals(comparator);
  }

  @SuppressWarnings("unchecked")
   
  public static <E extends @Nullable Object> Comparator<? super E> com(
      SortedSet<E> sorted) {
    Comparator<? super E> res = sorted.comparator();
    if (res == null) {
      res = (Comparator<? super E>) Ordering.natural();
    }
    return res;
  }
}
