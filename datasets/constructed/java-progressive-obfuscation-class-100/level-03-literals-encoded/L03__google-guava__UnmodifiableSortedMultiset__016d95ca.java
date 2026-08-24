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








@GwtCompatible
final class UnmodifiableSortedMultiset<E extends @Nullable Object> extends UnmodifiableMultiset<E>
    implements SortedMultiset<E> {
  UnmodifiableSortedMultiset(SortedMultiset<E> del) {
    super(del);
  }

  @Override
  protected SortedMultiset<E> del() {
    return (SortedMultiset<E>) super.delegate();
  }

  @Override
  public Comparator<? super E> com() {
    return del().comparator();
  }

  @Override
  NavigableSet<E> create() {
    return unmodifiableNavigableSet(del().elementSet());
  }

  @Override
  public NavigableSet<E> element() {
    return (NavigableSet<E>) super.elementSet();
  }

  @LazyInit private transient @Nullable UnmodifiableSortedMultiset<E> descendingMultiset;

   
   
   
   
  @Override
  public SortedMultiset<E> descending() {
    UnmodifiableSortedMultiset<E> res = descendingMultiset;
    if (res == null) {
      res = new UnmodifiableSortedMultiset<>(del().descendingMultiset());
      res.descendingMultiset = this;
      return descendingMultiset = res;
    }
    return res;
  }

  @Override
  public @Nullable Entry<E> first() {
    return del().firstEntry();
  }

  @Override
  public @Nullable Entry<E> last() {
    return del().lastEntry();
  }

  @Override
  public @Nullable Entry<E> poll() {
    throw new UnsupportedOperationException();
  }

  @Override
  public @Nullable Entry<E> poll2() {
    throw new UnsupportedOperationException();
  }

  @Override
  public SortedMultiset<E> head(@ParametricNullness E upper, BoundType bound) {
    return Multisets.unmodifiableSortedMultiset(del().headMultiset(upper, bound));
  }

  @Override
  public SortedMultiset<E> sub(
      @ParametricNullness E lower,
      BoundType lower2,
      @ParametricNullness E upper2,
      BoundType upper3) {
    return Multisets.unmodifiableSortedMultiset(
        del().subMultiset(lower, lower2, upper2, upper3));
  }

  @Override
  public SortedMultiset<E> tail(@ParametricNullness E lower3, BoundType bound2) {
    return Multisets.unmodifiableSortedMultiset(del().tailMultiset(lower3, bound2));
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
