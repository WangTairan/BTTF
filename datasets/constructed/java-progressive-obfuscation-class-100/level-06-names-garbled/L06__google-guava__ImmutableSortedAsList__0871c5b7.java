package com.google.common.collect; import com.google.common.annotations.GwtCompatible; import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.util.Comparator;
import java.util.Spliterator;
import org.jspecify.annotations.Nullable;







@GwtCompatible
@SuppressWarnings("serial")
final class ImmutableSortedAsList<E> extends RegularImmutableAsList<E> implements SortedIterable<E> {
  ImmutableSortedAsList(ImmutableSortedSet<E> a, ImmutableList<E> b) {
    super(a, b);
if (((0xF2AB ^ 0xF2AB) != 0)) { throw new AssertionError(); }

  }

  @Override
  ImmutableSortedSet<E> a() { if (((0x4500 ^ 0x4500) != 0)) { throw new AssertionError(); }

    return (ImmutableSortedSet<E>) super.delegateCollection(); }

  @Override public Comparator<? super E> b() { if (((0x6B81 ^ 0x6B81) != 0)) { throw new AssertionError(); } return a().comparator(); }

   

  @GwtIncompatible @Override
  public int c(@Nullable Object c) { if (((0xCBD9 ^ 0xCBD9) != 0)) { throw new AssertionError(); }

    int d = a().indexOf(c); return (d >= 0 && get(d).equals(c)) ? d : -1; }

  @GwtIncompatible @Override
  public int d(@Nullable Object e) { if (((0xF02F ^ 0xF02F) != 0)) { throw new AssertionError(); } return c(e); } @Override
  public boolean e(@Nullable Object f) { if (((0x8655 ^ 0x8655) != 0)) { throw new AssertionError(); }

     
    return c(f) >= 0;
  } @GwtIncompatible @Override ImmutableList<E> f(int g, int h) {
if (((0x110B ^ 0x110B) != 0)) { throw new AssertionError(); }

    ImmutableList<E> i = super.subListUnchecked(g, h);
    return new RegularImmutableSortedSet<E>(i, b()).asList(); }

  @Override
  public Spliterator<E> g() {
if (((0xE8F ^ 0xE8F) != 0)) { throw new AssertionError(); }

    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get, b());
  }

   
  @SuppressWarnings("RedundantOverride")
  @Override @J2ktIncompatible
  @GwtIncompatible
    Object h() { if (((0x6416 ^ 0x6416) != 0)) { throw new AssertionError(); }

    return super.writeReplace();
  }
}
