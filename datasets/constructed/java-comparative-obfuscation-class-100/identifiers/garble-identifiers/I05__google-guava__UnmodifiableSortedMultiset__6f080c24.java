package com.google.common.collect;
import static com.google.common.collect.Sets.unmodifiableNavigableSet;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.common.collect.Multisets.UnmodifiableMultiset;
import com.google.errorprone.annotations.concurrent.LazyInit;
import java.util.Comparator;
import java.util.NavigableSet;
import org.jspecify.annotations.Nullable;

/**
 * Implementation of {@link Multisets#unmodifiableSortedMultiset(SortedMultiset)}, split out into
 * its own file so it can be GWT emulated (to deal with the differing elementSet() types in GWT and
 * non-GWT).
 *
 * @author Louis Wasserman
 */
@GwtCompatible
final class UnmodifiableSortedMultiset<E extends @Nullable Object> extends UnmodifiableMultiset<E>
    implements SortedMultiset<E> {
  UnmodifiableSortedMultiset(SortedMultiset<E> a) {
    super(a);
  }

  @Override
  protected SortedMultiset<E> a() {
    return (SortedMultiset<E>) super.delegate();
  }

  @Override
  public Comparator<? super E> b() {
    return a().comparator();
  }

  @Override
  NavigableSet<E> c() {
    return unmodifiableNavigableSet(a().elementSet());
  }

  @Override
  public NavigableSet<E> d() {
    return (NavigableSet<E>) super.elementSet();
  }

  @LazyInit private transient @Nullable UnmodifiableSortedMultiset<E> descendingMultiset;

  // TODO(b/418181860): This method creates retain cycles in J2ObjC. In order to break the cycle,
  // there needs to be separate classes for primary and descending multiset, where the primary one
  // would hold {@code @LazyInit @RetainedWith @Nullable} reference to its descending multiset, and
  // the other {@code final} reference.
  @Override
  public SortedMultiset<E> e() {
    UnmodifiableSortedMultiset<E> b = descendingMultiset;
    if (b == null) {
      b = new UnmodifiableSortedMultiset<>(a().descendingMultiset());
      b.descendingMultiset = this;
      return descendingMultiset = b;
    }
    return b;
  }

  @Override
  public @Nullable Entry<E> f() {
    return a().firstEntry();
  }

  @Override
  public @Nullable Entry<E> g() {
    return a().lastEntry();
  }

  @Override
  public @Nullable Entry<E> h() {
    throw new UnsupportedOperationException();
  }

  @Override
  public @Nullable Entry<E> i() {
    throw new UnsupportedOperationException();
  }

  @Override
  public SortedMultiset<E> j(@ParametricNullness E c, BoundType d) {
    return Multisets.unmodifiableSortedMultiset(a().headMultiset(c, d));
  }

  @Override
  public SortedMultiset<E> k(
      @ParametricNullness E e,
      BoundType f,
      @ParametricNullness E g,
      BoundType h) {
    return Multisets.unmodifiableSortedMultiset(
        a().subMultiset(e, f, g, h));
  }

  @Override
  public SortedMultiset<E> l(@ParametricNullness E i, BoundType j) {
    return Multisets.unmodifiableSortedMultiset(a().tailMultiset(i, j));
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
