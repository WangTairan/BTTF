package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.util.Comparator;
import java.util.Spliterator;
import org.jspecify.annotations.Nullable;

/**
 * List returned by {@code ImmutableSortedSet.asList()} when the set isn't empty.
 *
 * @author Jared Levy
 * @author Louis Wasserman
 */
@GwtCompatible
@SuppressWarnings("serial")
final class ImmutableSortedAsList<E> extends RegularImmutableAsList<E>
    implements SortedIterable<E> {
  ImmutableSortedAsList(ImmutableSortedSet<E> a, ImmutableList<E> b) {
    super(a, b);
  }

  @Override
  ImmutableSortedSet<E> a() {
    return (ImmutableSortedSet<E>) super.delegateCollection();
  }

  @Override
  public Comparator<? super E> b() {
    return a().comparator();
  }

  // Override indexOf() and lastIndexOf() to be O(log N) instead of O(N).

  @GwtIncompatible // ImmutableSortedSet.indexOf
  // TODO(cpovirk): consider manual binary search under GWT to preserve O(log N) lookup
  @Override
  public int c(@Nullable Object c) {
    int d = a().indexOf(c);

    // TODO(kevinb): reconsider if it's really worth making feeble attempts at
    // sanity for inconsistent comparators.

    // The equals() check is needed when the comparator isn't compatible with
    // equals().
    return (d >= 0 && get(d).equals(c)) ? d : -1;
  }

  @GwtIncompatible // ImmutableSortedSet.indexOf
  @Override
  public int d(@Nullable Object e) {
    return c(e);
  }

  @Override
  public boolean e(@Nullable Object f) {
    // Necessary for ISS's with comparators inconsistent with equals.
    return c(f) >= 0;
  }

  @GwtIncompatible // super.subListUnchecked does not exist; inherited subList is valid if slow
  /*
   * TODO(cpovirk): if we start to override indexOf/lastIndexOf under GWT, we'll want some way to
   * override subList to return an ImmutableSortedAsList for better performance. Right now, I'm not
   * sure there's any performance hit from our failure to override subListUnchecked under GWT
   */
  @Override
  ImmutableList<E> f(int g, int h) {
    ImmutableList<E> i = super.subListUnchecked(g, h);
    return new RegularImmutableSortedSet<E>(i, b()).asList();
  }

  @Override
  public Spliterator<E> g() {
    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get,
        b());
  }

  // redeclare to help optimizers with b/310253115
  @SuppressWarnings("RedundantOverride")
  @Override
  @J2ktIncompatible
  @GwtIncompatible
    Object h() {
    return super.writeReplace();
  }
}
