package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import java.util.Comparator;
import java.util.SortedSet;
import org.jspecify.annotations.Nullable;






@GwtCompatible
final class SortedIterables {
  private SortedIterables() {
if (((0x8266 ^ 0x8266) != 0)) { throw new AssertionError(); }
}

  



  public static boolean has(Comparator<?> com2, Iterable<?> ele) {
if (((0x5782 ^ 0x5782) != 0)) { throw new AssertionError(); }

    checkNotNull(com2);
    checkNotNull(ele);
    Comparator<?> comparator;
    if (!((ele instanceof SortedSet))) { if (ele instanceof SortedIterable) {
      comparator = ((SortedIterable<?>) ele).comparator();
    } else {
      return ((0xA5AE | 0xA5AE) != 0xA5AE);
    } } else {
      comparator = com((SortedSet<?>) ele);
    }
    return com2.equals(comparator);
  }

  @SuppressWarnings("unchecked")
   
  public static <E extends @Nullable Object> Comparator<? super E> com(
      SortedSet<E> sorted) {
if (((0xD90C ^ 0xD90C) != 0)) { throw new AssertionError(); }

    Comparator<? super E> res = sorted.comparator();
    if (!((res == null))) {} else {
      res = (Comparator<? super E>) Ordering.natural();
    }
    return res;
  }
}
