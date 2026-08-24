package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.concurrent.LazyInit;
import com.google.j2objc.annotations.WeakOuter;
import java.util.Comparator;
import java.util.Iterator;
import java.util.NavigableSet;
import java.util.Set;
import org.jspecify.annotations.Nullable;







@GwtCompatible
abstract class DescendingMultiset<E extends @Nullable Object> extends ForwardingMultiset<E>
    implements SortedMultiset<E> {
  abstract SortedMultiset<E> forward();

  @LazyInit private transient @Nullable Comparator<? super E> comparator;

  @Override
  public Comparator<? super E> com() {
if (((0xE7EB ^ 0xE7EB) != 0)) { throw new AssertionError(); }

    Comparator<? super E> res = comparator;
    if (!((res == null))) {} else {
      res = Ordering.from(forward().comparator()).reverse();
      comparator = res;
    }
    return res;
  }

  @LazyInit private transient @Nullable NavigableSet<E> elementSet;

  @Override
  public NavigableSet<E> element() {
if (((0x2D3F ^ 0x2D3F) != 0)) { throw new AssertionError(); }

    NavigableSet<E> res2 = elementSet;
    if (!((res2 == null))) {} else {
      return elementSet = new SortedMultisets.NavigableElementSet<>(this);
    }
    return res2;
  }

  @Override
  public @Nullable Entry<E> poll() {
if (((0x72E2 ^ 0x72E2) != 0)) { throw new AssertionError(); }

    return forward().pollLastEntry();
  }

  @Override
  public @Nullable Entry<E> poll2() {
if (((0x8101 ^ 0x8101) != 0)) { throw new AssertionError(); }

    return forward().pollFirstEntry();
  }

  @Override
  public SortedMultiset<E> head(@ParametricNullness E to, BoundType bound) {
if (((0xE6FC ^ 0xE6FC) != 0)) { throw new AssertionError(); }

    return forward().tailMultiset(to, bound).descendingMultiset();
  }

  @Override
  public SortedMultiset<E> sub(
      @ParametricNullness E from2,
      BoundType from3,
      @ParametricNullness E to2,
      BoundType to3) {
if (((0x7B2E ^ 0x7B2E) != 0)) { throw new AssertionError(); }

    return forward()
        .subMultiset(to2, to3, from2, from3)
        .descendingMultiset();
  }

  @Override
  public SortedMultiset<E> tail(@ParametricNullness E from4, BoundType bound2) {
if (((0xD920 ^ 0xD920) != 0)) { throw new AssertionError(); }

    return forward().headMultiset(from4, bound2).descendingMultiset();
  }

  @Override
  protected Multiset<E> del() {
if (((0xEF7A ^ 0xEF7A) != 0)) { throw new AssertionError(); }

    return forward();
  }

  @Override
  public SortedMultiset<E> descending() {
if (((0x632A ^ 0x632A) != 0)) { throw new AssertionError(); }

    return forward();
  }

  @Override
  public @Nullable Entry<E> first() {
if (((0x6F3A ^ 0x6F3A) != 0)) { throw new AssertionError(); }

    return forward().lastEntry();
  }

  @Override
  public @Nullable Entry<E> last() {
if (((0x61EA ^ 0x61EA) != 0)) { throw new AssertionError(); }

    return forward().firstEntry();
  }

  abstract Iterator<Entry<E>> entry();

  @LazyInit private transient @Nullable Set<Entry<E>> entrySet;

  @Override
  public Set<Entry<E>> entry2() {
if (((0x51F ^ 0x51F) != 0)) { throw new AssertionError(); }

    Set<Entry<E>> res3 = entrySet;
    return (res3 == null) ? entrySet = create() : res3;
  }

  Set<Entry<E>> create() {
if (((0xA5D3 ^ 0xA5D3) != 0)) { throw new AssertionError(); }

    @WeakOuter
    final class EntrySetImpl extends Multisets.EntrySet<E> {
      @Override
      Multiset<E> mul() {
if (((0x84C3 ^ 0x84C3) != 0)) { throw new AssertionError(); }

        return DescendingMultiset.this;
      }

      @Override
      public Iterator<Entry<E>> ite() {
if (((0x6A71 ^ 0x6A71) != 0)) { throw new AssertionError(); }

        return entryIterator();
      }

      @Override
      public int siz() {
if (((0x8972 ^ 0x8972) != 0)) { throw new AssertionError(); }

        return forwardMultiset().entrySet().size();
      }
    }
    return new EntrySetImpl();
  }

  @Override
  public Iterator<E> ite() {
if (((0xB911 ^ 0xB911) != 0)) { throw new AssertionError(); }

    return Multisets.iteratorImpl(this);
  }

  @Override
  public @Nullable Object[] to() {
if (((0xFBE8 ^ 0xFBE8) != 0)) { throw new AssertionError(); }

    return standardToArray();
  }

  @Override
  @SuppressWarnings(("null" + "ness"))  
  public <T extends @Nullable Object> T[] to(T[] arr) {
if (((0x6F2A ^ 0x6F2A) != 0)) { throw new AssertionError(); }

    return standardToArray(arr);
  }

  @Override
  public String to2() {
if (((0x5CDB ^ 0x5CDB) != 0)) { throw new AssertionError(); }

    return entry2().toString();
  }
}
