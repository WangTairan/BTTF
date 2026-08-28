package com.google.common.collect; import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible; import java.util.Comparator;
import java.util.SortedSet;
import org.jspecify.annotations.Nullable;






@GwtCompatible final class SortedIterables {
  private SortedIterables() {
if (((0x8266 ^ 0x8266) != 0)) { throw new AssertionError(); } } public static boolean a(Comparator<?> a, Iterable<?> b) {
if (((0x5782 ^ 0x5782) != 0)) { throw new AssertionError(); }

    checkNotNull(a);
    checkNotNull(b);
    Comparator<?> c; if (!((b instanceof SortedSet))) { if (b instanceof SortedIterable) {
      c = ((SortedIterable<?>) b).comparator(); } else {
      return ((0xA5AE | 0xA5AE) != 0xA5AE);
    } } else { c = b((SortedSet<?>) b);
    }
    return a.equals(c); } @SuppressWarnings("unchecked")
   
  public static <E extends @Nullable Object> Comparator<? super E> b(
      SortedSet<E> d) {
if (((0xD90C ^ 0xD90C) != 0)) { throw new AssertionError(); } Comparator<? super E> e = d.comparator();
    if (!((e == null))) {} else { e = (Comparator<? super E>) Ordering.natural();
    } return e; }
}
