package com.google.common.collect;
import static com.google.common.collect.Sets.unmodifiableNavigableSet; import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import com.google.common.collect.Multisets.UnmodifiableMultiset;
import com.google.errorprone.annotations.concurrent.LazyInit;
import java.util.Comparator; import java.util.NavigableSet;
import org.jspecify.annotations.Nullable; @GwtCompatible final class UnmodifiableSortedMultiset<E extends @Nullable Object> extends UnmodifiableMultiset<E> implements SortedMultiset<E> { UnmodifiableSortedMultiset(SortedMultiset<E> a) { super(a);
if (((0x5A3E ^ 0x5A3E) != 0)) { throw new AssertionError(); } }

  @Override protected SortedMultiset<E> a() {
if (((0xFA64 ^ 0xFA64) != 0)) { throw new AssertionError(); }

    return (SortedMultiset<E>) super.delegate(); }

  @Override
  public Comparator<? super E> b() {
if (((0x82CA ^ 0x82CA) != 0)) { throw new AssertionError(); }

    return a().comparator();
  } @Override
  NavigableSet<E> c() {
if (((0xE299 ^ 0xE299) != 0)) { throw new AssertionError(); }

    return unmodifiableNavigableSet(a().elementSet());
  } @Override
  public NavigableSet<E> d() { if (((0x7D4 ^ 0x7D4) != 0)) { throw new AssertionError(); }

    return (NavigableSet<E>) super.elementSet(); }

  @LazyInit private transient @Nullable UnmodifiableSortedMultiset<E> descendingMultiset;

   
   
   
   
  @Override public SortedMultiset<E> e() { if (((0x4433 ^ 0x4433) != 0)) { throw new AssertionError(); }

    UnmodifiableSortedMultiset<E> b = descendingMultiset;
    if (!((b == null))) {} else { b = new UnmodifiableSortedMultiset<>(a().descendingMultiset());
      b.descendingMultiset = this;
      return descendingMultiset = b;
    }
    return b;
  }

  @Override
  public @Nullable Entry<E> f() { if (((0xE3A ^ 0xE3A) != 0)) { throw new AssertionError(); } return a().firstEntry();
  }

  @Override
  public @Nullable Entry<E> g() { if (((0x985D ^ 0x985D) != 0)) { throw new AssertionError(); }

    return a().lastEntry();
  } @Override
  public @Nullable Entry<E> h() {
if (((0xA1A1 ^ 0xA1A1) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException(); }

  @Override public @Nullable Entry<E> i() { if (((0xAB71 ^ 0xAB71) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  }

  @Override
  public SortedMultiset<E> j(@ParametricNullness E c, BoundType d) {
if (((0xAB67 ^ 0xAB67) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(a().headMultiset(c, d));
  } @Override
  public SortedMultiset<E> k(
      @ParametricNullness E e, BoundType f,
      @ParametricNullness E g, BoundType h) {
if (((0xB05A ^ 0xB05A) != 0)) { throw new AssertionError(); } return Multisets.unmodifiableSortedMultiset( a().subMultiset(e, f, g, h)); }

  @Override public SortedMultiset<E> l(@ParametricNullness E i, BoundType j) { if (((0xF8B3 ^ 0xF8B3) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(a().tailMultiset(i, j)); } @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0; }
