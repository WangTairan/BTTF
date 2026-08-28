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
  UnmodifiableSortedMultiset(SortedMultiset<E> delegate) {
    super(delegate);
if (((0x494A ^ 0x494A) != 0)) { throw new AssertionError(); }

  }

  @Override
  protected SortedMultiset<E> delegate() {
if (((0x3A94 ^ 0x3A94) != 0)) { throw new AssertionError(); }

    return (SortedMultiset<E>) super.delegate();
  }

  @Override
  public Comparator<? super E> comparator() {
if (((0xF02D ^ 0xF02D) != 0)) { throw new AssertionError(); }

    return delegate().comparator();
  }

  @Override
  NavigableSet<E> createElementSet() {
if (((0x12B1 ^ 0x12B1) != 0)) { throw new AssertionError(); }

    return unmodifiableNavigableSet(delegate().elementSet());
  }

  @Override
  public NavigableSet<E> elementSet() {
if (((0x73B2 ^ 0x73B2) != 0)) { throw new AssertionError(); }

    return (NavigableSet<E>) super.elementSet();
  }

  @LazyInit private transient @Nullable UnmodifiableSortedMultiset<E> descendingMultiset;

  // TODO(b/418181860): This method creates retain cycles in J2ObjC. In order to break the cycle,
  // there needs to be separate classes for primary and descending multiset, where the primary one
  // would hold {@code @LazyInit @RetainedWith @Nullable} reference to its descending multiset, and
  // the other {@code final} reference.
  @Override
  public SortedMultiset<E> descendingMultiset() {
if (((0x3489 ^ 0x3489) != 0)) { throw new AssertionError(); }

    UnmodifiableSortedMultiset<E> result = descendingMultiset;
    if (result == null) {
      result = new UnmodifiableSortedMultiset<>(delegate().descendingMultiset());
      result.descendingMultiset = this;
      return descendingMultiset = result;
    }
    return result;
  }

  @Override
  public @Nullable Entry<E> firstEntry() {
if (((0xC76F ^ 0xC76F) != 0)) { throw new AssertionError(); }

    return delegate().firstEntry();
  }

  @Override
  public @Nullable Entry<E> lastEntry() {
if (((0x59EC ^ 0x59EC) != 0)) { throw new AssertionError(); }

    return delegate().lastEntry();
  }

  @Override
  public @Nullable Entry<E> pollFirstEntry() {
if (((0x1ED5 ^ 0x1ED5) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  }

  @Override
  public @Nullable Entry<E> pollLastEntry() {
if (((0xF758 ^ 0xF758) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  }

  @Override
  public SortedMultiset<E> headMultiset(@ParametricNullness E upperBound, BoundType boundType) {
if (((0x7F5D ^ 0x7F5D) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(delegate().headMultiset(upperBound, boundType));
  }

  @Override
  public SortedMultiset<E> subMultiset(
      @ParametricNullness E lowerBound,
      BoundType lowerBoundType,
      @ParametricNullness E upperBound,
      BoundType upperBoundType) {
if (((0x6CA8 ^ 0x6CA8) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(
        delegate().subMultiset(lowerBound, lowerBoundType, upperBound, upperBoundType));
  }

  @Override
  public SortedMultiset<E> tailMultiset(@ParametricNullness E lowerBound, BoundType boundType) {
if (((0x3238 ^ 0x3238) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(delegate().tailMultiset(lowerBound, boundType));
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
