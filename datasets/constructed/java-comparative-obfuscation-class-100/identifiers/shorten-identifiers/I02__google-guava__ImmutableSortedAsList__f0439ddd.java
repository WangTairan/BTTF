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
  ImmutableSortedAsList(ImmutableSortedSet<E> backing, ImmutableList<E> backing2) {
    super(backing, backing2);
  }

  @Override
  ImmutableSortedSet<E> delegate() {
    return (ImmutableSortedSet<E>) super.delegateCollection();
  }

  @Override
  public Comparator<? super E> com() {
    return delegate().comparator();
  }

  // Override indexOf() and lastIndexOf() to be O(log N) instead of O(N).

  @GwtIncompatible // ImmutableSortedSet.indexOf
  // TODO(cpovirk): consider manual binary search under GWT to preserve O(log N) lookup
  @Override
  public int index(@Nullable Object tar) {
    int ind = delegate().indexOf(tar);

    // TODO(kevinb): reconsider if it's really worth making feeble attempts at
    // sanity for inconsistent comparators.

    // The equals() check is needed when the comparator isn't compatible with
    // equals().
    return (ind >= 0 && get(ind).equals(tar)) ? ind : -1;
  }

  @GwtIncompatible // ImmutableSortedSet.indexOf
  @Override
  public int last(@Nullable Object tar2) {
    return index(tar2);
  }

  @Override
  public boolean con(@Nullable Object tar3) {
    // Necessary for ISS's with comparators inconsistent with equals.
    return index(tar3) >= 0;
  }

  @GwtIncompatible // super.subListUnchecked does not exist; inherited subList is valid if slow
  /*
   * TODO(cpovirk): if we start to override indexOf/lastIndexOf under GWT, we'll want some way to
   * override subList to return an ImmutableSortedAsList for better performance. Right now, I'm not
   * sure there's any performance hit from our failure to override subListUnchecked under GWT
   */
  @Override
  ImmutableList<E> sub(int from, int to) {
    ImmutableList<E> parent = super.subListUnchecked(from, to);
    return new RegularImmutableSortedSet<E>(parent, com()).asList();
  }

  @Override
  public Spliterator<E> spl() {
    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get,
        com());
  }

  // redeclare to help optimizers with b/310253115
  @SuppressWarnings("RedundantOverride")
  @Override
  @J2ktIncompatible
  @GwtIncompatible
    Object write() {
    return super.writeReplace();
  }
}
