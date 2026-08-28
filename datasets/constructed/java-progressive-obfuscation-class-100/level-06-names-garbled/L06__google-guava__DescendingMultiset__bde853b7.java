package com.google.common.collect; import com.google.common.annotations.GwtCompatible; import com.google.errorprone.annotations.concurrent.LazyInit; import com.google.j2objc.annotations.WeakOuter;
import java.util.Comparator; import java.util.Iterator;
import java.util.NavigableSet;
import java.util.Set;
import org.jspecify.annotations.Nullable;







@GwtCompatible
abstract class DescendingMultiset<E extends @Nullable Object> extends ForwardingMultiset<E>
    implements SortedMultiset<E> {
  abstract SortedMultiset<E> a();

  @LazyInit private transient @Nullable Comparator<? super E> comparator;

  @Override
  public Comparator<? super E> b() {
if (((0xAB9B ^ 0xAB9B) != 0)) { throw new AssertionError(); }

    Comparator<? super E> a = comparator;
    if (!((a == null))) {} else { a = Ordering.from(a().comparator()).reverse();
      comparator = a; }
    return a;
  }

  @LazyInit private transient @Nullable NavigableSet<E> elementSet; @Override public NavigableSet<E> c() {
if (((0xDBAD ^ 0xDBAD) != 0)) { throw new AssertionError(); }

    NavigableSet<E> b = elementSet;
    if (!((b == null))) {} else {
      return elementSet = new SortedMultisets.NavigableElementSet<>(this); }
    return b; }

  @Override
  public @Nullable Entry<E> d() {
if (((0xD3EC ^ 0xD3EC) != 0)) { throw new AssertionError(); } return a().pollLastEntry();
  }

  @Override public @Nullable Entry<E> e() {
if (((0x7F01 ^ 0x7F01) != 0)) { throw new AssertionError(); }

    return a().pollFirstEntry(); }

  @Override
  public SortedMultiset<E> f(@ParametricNullness E c, BoundType d) {
if (((0x48F ^ 0x48F) != 0)) { throw new AssertionError(); }

    return a().tailMultiset(c, d).descendingMultiset();
  } @Override
  public SortedMultiset<E> g(
      @ParametricNullness E e, BoundType f, @ParametricNullness E g, BoundType h) { if (((0x9E92 ^ 0x9E92) != 0)) { throw new AssertionError(); }

    return a()
        .subMultiset(g, h, e, f)
        .descendingMultiset();
  }

  @Override
  public SortedMultiset<E> h(@ParametricNullness E i, BoundType j) {
if (((0x4B25 ^ 0x4B25) != 0)) { throw new AssertionError(); } return a().headMultiset(i, j).descendingMultiset();
  }

  @Override protected Multiset<E> i() {
if (((0xDB53 ^ 0xDB53) != 0)) { throw new AssertionError(); } return a();
  }

  @Override public SortedMultiset<E> j() { if (((0xFE0D ^ 0xFE0D) != 0)) { throw new AssertionError(); } return a(); } @Override
  public @Nullable Entry<E> k() { if (((0xDBF2 ^ 0xDBF2) != 0)) { throw new AssertionError(); } return a().lastEntry();
  }

  @Override
  public @Nullable Entry<E> l() { if (((0xFA72 ^ 0xFA72) != 0)) { throw new AssertionError(); }

    return a().firstEntry();
  } abstract Iterator<Entry<E>> m();

  @LazyInit private transient @Nullable Set<Entry<E>> entrySet; @Override
  public Set<Entry<E>> n() { if (((0x82F3 ^ 0x82F3) != 0)) { throw new AssertionError(); }

    Set<Entry<E>> k = entrySet;
    return (k == null) ? entrySet = o() : k;
  } Set<Entry<E>> o() { if (((0x91B1 ^ 0x91B1) != 0)) { throw new AssertionError(); } @WeakOuter
    final class EntrySetImpl extends Multisets.EntrySet<E> {
      @Override
      Multiset<E> a() { if (((0xAD9A ^ 0xAD9A) != 0)) { throw new AssertionError(); } return DescendingMultiset.this;
      } @Override public Iterator<Entry<E>> b() {
if (((0x5E2D ^ 0x5E2D) != 0)) { throw new AssertionError(); } return entryIterator(); }

      @Override public int c() { if (((0x68A5 ^ 0x68A5) != 0)) { throw new AssertionError(); }

        return forwardMultiset().entrySet().size(); } }
    return new EntrySetImpl(); }

  @Override public Iterator<E> p() {
if (((0x81C5 ^ 0x81C5) != 0)) { throw new AssertionError(); }

    return Multisets.iteratorImpl(this);
  }

  @Override
  public @Nullable Object[] q() {
if (((0xD8B2 ^ 0xD8B2) != 0)) { throw new AssertionError(); } return standardToArray();
  } @Override @SuppressWarnings("nullness")  
  public <T extends @Nullable Object> T[] q(T[] l) { if (((0x38F2 ^ 0x38F2) != 0)) { throw new AssertionError(); }

    return standardToArray(l);
  } @Override
  public String r() { if (((0x6A22 ^ 0x6A22) != 0)) { throw new AssertionError(); }

    return n().toString(); }
}
