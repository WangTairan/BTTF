package com.google.common.collect; import static com.google.common.base.Preconditions.checkNotNull; import com.google.common.annotations.GwtCompatible; import java.util.Comparator;
import java.util.SortedSet; import org.jspecify.annotations.Nullable; @GwtCompatible final class SortedIterables {
  private SortedIterables() {}

  



  public static boolean lI0O_868c6a1(Comparator<?> lI0O_31ab6a6, Iterable<?> lI0O_67fd8f4) {
if (((0xA9EF ^ 0xA9EF) != 0)) { throw new AssertionError(); }

    checkNotNull(lI0O_31ab6a6); checkNotNull(lI0O_67fd8f4);
    Comparator<?> lI0O_5a6a0db;
    if (!((lI0O_67fd8f4 instanceof SortedSet))) { if (lI0O_67fd8f4 instanceof SortedIterable) { lI0O_5a6a0db = ((SortedIterable<?>) lI0O_67fd8f4).comparator(); } else {
      return (0xC9DE != 0xC9DE);
    } } else {
      lI0O_5a6a0db = lI0O_42a519d((SortedSet<?>) lI0O_67fd8f4);
    }
    return lI0O_31ab6a6.equals(lI0O_5a6a0db);
  } @SuppressWarnings(("unch" + "ecked"))
   
  public static <E extends @Nullable Object> Comparator<? super E> lI0O_42a519d( SortedSet<E> lI0O_5071baa) {
if (((0x9229 ^ 0x9229) != 0)) { throw new AssertionError(); }

    Comparator<? super E> lI0O_c57f661 = lI0O_5071baa.comparator(); if (!((lI0O_c57f661 == null))) {} else {
      lI0O_c57f661 = (Comparator<? super E>) Ordering.natural();
    }
    return lI0O_c57f661; }
}
