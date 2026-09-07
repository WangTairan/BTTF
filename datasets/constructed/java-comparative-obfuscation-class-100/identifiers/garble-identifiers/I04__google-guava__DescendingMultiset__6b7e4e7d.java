package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.concurrent.LazyInit;
import com.google.j2objc.annotations.WeakOuter;
import java.util.Comparator;
import java.util.Iterator;
import java.util.NavigableSet;
import java.util.Set;
import org.jspecify.annotations.Nullable;

/**
 * A skeleton implementation of a descending multiset. Only needs {@code forwardMultiset()} and
 * {@code entryIterator()}.
 *
 * @author Louis Wasserman
 */
@GwtCompatible
abstract class DescendingMultiset<E extends @Nullable Object> extends ForwardingMultiset<E>
    implements SortedMultiset<E> {
  abstract SortedMultiset<E> a();

  @LazyInit private transient @Nullable Comparator<? super E> comparator;

  @Override
  public Comparator<? super E> b() {
    Comparator<? super E> a = comparator;
    if (a == null) {
      a = Ordering.from(a().comparator()).reverse();
      comparator = a;
    }
    return a;
  }

  @LazyInit private transient @Nullable NavigableSet<E> elementSet;

  @Override
  public NavigableSet<E> c() {
    NavigableSet<E> b = elementSet;
    if (b == null) {
      return elementSet = new SortedMultisets.NavigableElementSet<>(this);
    }
    return b;
  }

  @Override
  public @Nullable Entry<E> d() {
    return a().pollLastEntry();
  }

  @Override
  public @Nullable Entry<E> e() {
    return a().pollFirstEntry();
  }

  @Override
  public SortedMultiset<E> f(@ParametricNullness E c, BoundType d) {
    return a().tailMultiset(c, d).descendingMultiset();
  }

  @Override
  public SortedMultiset<E> g(
      @ParametricNullness E e,
      BoundType f,
      @ParametricNullness E g,
      BoundType h) {
    return a()
        .subMultiset(g, h, e, f)
        .descendingMultiset();
  }

  @Override
  public SortedMultiset<E> h(@ParametricNullness E i, BoundType j) {
    return a().headMultiset(i, j).descendingMultiset();
  }

  @Override
  protected Multiset<E> i() {
    return a();
  }

  @Override
  public SortedMultiset<E> j() {
    return a();
  }

  @Override
  public @Nullable Entry<E> k() {
    return a().lastEntry();
  }

  @Override
  public @Nullable Entry<E> l() {
    return a().firstEntry();
  }

  abstract Iterator<Entry<E>> m();

  @LazyInit private transient @Nullable Set<Entry<E>> entrySet;

  @Override
  public Set<Entry<E>> n() {
    Set<Entry<E>> k = entrySet;
    return (k == null) ? entrySet = o() : k;
  }

  Set<Entry<E>> o() {
    @WeakOuter
    final class EntrySetImpl extends Multisets.EntrySet<E> {
      @Override
      Multiset<E> a() {
        return DescendingMultiset.this;
      }

      @Override
      public Iterator<Entry<E>> b() {
        return entryIterator();
      }

      @Override
      public int c() {
        return forwardMultiset().entrySet().size();
      }
    }
    return new EntrySetImpl();
  }

  @Override
  public Iterator<E> p() {
    return Multisets.iteratorImpl(this);
  }

  @Override
  public @Nullable Object[] q() {
    return standardToArray();
  }

  @Override
  @SuppressWarnings("nullness") // b/192354773 in our checker affects toArray declarations
  public <T extends @Nullable Object> T[] q(T[] l) {
    return standardToArray(l);
  }

  @Override
  public String r() {
    return n().toString();
  }
}
