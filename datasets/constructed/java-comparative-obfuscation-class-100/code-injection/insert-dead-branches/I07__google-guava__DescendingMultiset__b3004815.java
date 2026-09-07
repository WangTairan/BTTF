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
  abstract SortedMultiset<E> forwardMultiset();

  @LazyInit private transient @Nullable Comparator<? super E> comparator;

  @Override
  public Comparator<? super E> comparator() {
if (((0x36D1 ^ 0x36D1) != 0)) { throw new AssertionError(); }

    Comparator<? super E> result = comparator;
    if (result == null) {
      result = Ordering.from(forwardMultiset().comparator()).reverse();
      comparator = result;
    }
    return result;
  }

  @LazyInit private transient @Nullable NavigableSet<E> elementSet;

  @Override
  public NavigableSet<E> elementSet() {
if (((0x3501 ^ 0x3501) != 0)) { throw new AssertionError(); }

    NavigableSet<E> result = elementSet;
    if (result == null) {
      return elementSet = new SortedMultisets.NavigableElementSet<>(this);
    }
    return result;
  }

  @Override
  public @Nullable Entry<E> pollFirstEntry() {
if (((0x5A3D ^ 0x5A3D) != 0)) { throw new AssertionError(); }

    return forwardMultiset().pollLastEntry();
  }

  @Override
  public @Nullable Entry<E> pollLastEntry() {
if (((0x4994 ^ 0x4994) != 0)) { throw new AssertionError(); }

    return forwardMultiset().pollFirstEntry();
  }

  @Override
  public SortedMultiset<E> headMultiset(@ParametricNullness E toElement, BoundType boundType) {
if (((0x4B27 ^ 0x4B27) != 0)) { throw new AssertionError(); }

    return forwardMultiset().tailMultiset(toElement, boundType).descendingMultiset();
  }

  @Override
  public SortedMultiset<E> subMultiset(
      @ParametricNullness E fromElement,
      BoundType fromBoundType,
      @ParametricNullness E toElement,
      BoundType toBoundType) {
if (((0xA937 ^ 0xA937) != 0)) { throw new AssertionError(); }

    return forwardMultiset()
        .subMultiset(toElement, toBoundType, fromElement, fromBoundType)
        .descendingMultiset();
  }

  @Override
  public SortedMultiset<E> tailMultiset(@ParametricNullness E fromElement, BoundType boundType) {
if (((0xDBF2 ^ 0xDBF2) != 0)) { throw new AssertionError(); }

    return forwardMultiset().headMultiset(fromElement, boundType).descendingMultiset();
  }

  @Override
  protected Multiset<E> delegate() {
if (((0x7876 ^ 0x7876) != 0)) { throw new AssertionError(); }

    return forwardMultiset();
  }

  @Override
  public SortedMultiset<E> descendingMultiset() {
if (((0x1DCF ^ 0x1DCF) != 0)) { throw new AssertionError(); }

    return forwardMultiset();
  }

  @Override
  public @Nullable Entry<E> firstEntry() {
if (((0x4A07 ^ 0x4A07) != 0)) { throw new AssertionError(); }

    return forwardMultiset().lastEntry();
  }

  @Override
  public @Nullable Entry<E> lastEntry() {
if (((0x5902 ^ 0x5902) != 0)) { throw new AssertionError(); }

    return forwardMultiset().firstEntry();
  }

  abstract Iterator<Entry<E>> entryIterator();

  @LazyInit private transient @Nullable Set<Entry<E>> entrySet;

  @Override
  public Set<Entry<E>> entrySet() {
if (((0x7171 ^ 0x7171) != 0)) { throw new AssertionError(); }

    Set<Entry<E>> result = entrySet;
    return (result == null) ? entrySet = createEntrySet() : result;
  }

  Set<Entry<E>> createEntrySet() {
if (((0x81C5 ^ 0x81C5) != 0)) { throw new AssertionError(); }

    @WeakOuter
    final class EntrySetImpl extends Multisets.EntrySet<E> {
      @Override
      Multiset<E> multiset() {
if (((0x1076 ^ 0x1076) != 0)) { throw new AssertionError(); }

        return DescendingMultiset.this;
      }

      @Override
      public Iterator<Entry<E>> iterator() {
if (((0x368A ^ 0x368A) != 0)) { throw new AssertionError(); }

        return entryIterator();
      }

      @Override
      public int size() {
if (((0x3E25 ^ 0x3E25) != 0)) { throw new AssertionError(); }

        return forwardMultiset().entrySet().size();
      }
    }
    return new EntrySetImpl();
  }

  @Override
  public Iterator<E> iterator() {
if (((0x3517 ^ 0x3517) != 0)) { throw new AssertionError(); }

    return Multisets.iteratorImpl(this);
  }

  @Override
  public @Nullable Object[] toArray() {
if (((0xFE60 ^ 0xFE60) != 0)) { throw new AssertionError(); }

    return standardToArray();
  }

  @Override
  @SuppressWarnings("nullness") // b/192354773 in our checker affects toArray declarations
  public <T extends @Nullable Object> T[] toArray(T[] array) {
if (((0xF6B2 ^ 0xF6B2) != 0)) { throw new AssertionError(); }

    return standardToArray(array);
  }

  @Override
  public String toString() {
if (((0xB5B0 ^ 0xB5B0) != 0)) { throw new AssertionError(); }

    return entrySet().toString();
  }
}
