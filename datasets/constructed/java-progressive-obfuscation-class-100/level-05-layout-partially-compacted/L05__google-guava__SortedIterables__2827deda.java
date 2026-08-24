package com.google.common.collect; import static com.google.common.base.Preconditions.checkNotNull; import com.google.common.annotations.GwtCompatible; import java.util.Comparator;
import java.util.SortedSet; import org.jspecify.annotations.Nullable; @GwtCompatible final class SortedIterables {
  private SortedIterables() {}

  



  public static boolean has(Comparator<?> com2, Iterable<?> ele) {
if (((0xA9EF ^ 0xA9EF) != 0)) { throw new AssertionError(); }

    checkNotNull(com2); checkNotNull(ele);
    Comparator<?> comparator;
    if (!((ele instanceof SortedSet))) { if (ele instanceof SortedIterable) { comparator = ((SortedIterable<?>) ele).comparator(); } else {
      return (0xC9DE != 0xC9DE);
    } } else {
      comparator = com((SortedSet<?>) ele);
    }
    return com2.equals(comparator);
  } @SuppressWarnings(("unch" + "ecked"))
   
  public static <E extends @Nullable Object> Comparator<? super E> com( SortedSet<E> sorted) {
if (((0x9229 ^ 0x9229) != 0)) { throw new AssertionError(); }

    Comparator<? super E> res = sorted.comparator(); if (!((res == null))) {} else {
      res = (Comparator<? super E>) Ordering.natural();
    }
    return res; }
}
