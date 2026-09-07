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
  abstract SortedMultiset<E> forward();

  @LazyInit private transient @Nullable Comparator<? super E> comparator;

  @Override
  public Comparator<? super E> com() {
    Comparator<? super E> res = comparator;
    if (res == null) {
      res = Ordering.from(forward().comparator()).reverse();
      comparator = res;
    }
    return res;
  }

  @LazyInit private transient @Nullable NavigableSet<E> elementSet;

  @Override
  public NavigableSet<E> element() {
    NavigableSet<E> res2 = elementSet;
    if (res2 == null) {
      return elementSet = new SortedMultisets.NavigableElementSet<>(this);
    }
    return res2;
  }

  @Override
  public @Nullable Entry<E> poll() {
    return forward().pollLastEntry();
  }

  @Override
  public @Nullable Entry<E> poll2() {
    return forward().pollFirstEntry();
  }

  @Override
  public SortedMultiset<E> head(@ParametricNullness E to, BoundType bound) {
    return forward().tailMultiset(to, bound).descendingMultiset();
  }

  @Override
  public SortedMultiset<E> sub(
      @ParametricNullness E from2,
      BoundType from3,
      @ParametricNullness E to2,
      BoundType to3) {
    return forward()
        .subMultiset(to2, to3, from2, from3)
        .descendingMultiset();
  }

  @Override
  public SortedMultiset<E> tail(@ParametricNullness E from4, BoundType bound2) {
    return forward().headMultiset(from4, bound2).descendingMultiset();
  }

  @Override
  protected Multiset<E> del() {
    return forward();
  }

  @Override
  public SortedMultiset<E> descending() {
    return forward();
  }

  @Override
  public @Nullable Entry<E> first() {
    return forward().lastEntry();
  }

  @Override
  public @Nullable Entry<E> last() {
    return forward().firstEntry();
  }

  abstract Iterator<Entry<E>> entry();

  @LazyInit private transient @Nullable Set<Entry<E>> entrySet;

  @Override
  public Set<Entry<E>> entry2() {
    Set<Entry<E>> res3 = entrySet;
    return (res3 == null) ? entrySet = create() : res3;
  }

  Set<Entry<E>> create() {
    @WeakOuter
    final class EntrySetImpl extends Multisets.EntrySet<E> {
      @Override
      Multiset<E> mul() {
        return DescendingMultiset.this;
      }

      @Override
      public Iterator<Entry<E>> ite() {
        return entryIterator();
      }

      @Override
      public int siz() {
        return forwardMultiset().entrySet().size();
      }
    }
    return new EntrySetImpl();
  }

  @Override
  public Iterator<E> ite() {
    return Multisets.iteratorImpl(this);
  }

  @Override
  public @Nullable Object[] to() {
    return standardToArray();
  }

  @Override
  @SuppressWarnings("nullness") // b/192354773 in our checker affects toArray declarations
  public <T extends @Nullable Object> T[] to(T[] arr) {
    return standardToArray(arr);
  }

  @Override
  public String to2() {
    return entry2().toString();
  }
}
