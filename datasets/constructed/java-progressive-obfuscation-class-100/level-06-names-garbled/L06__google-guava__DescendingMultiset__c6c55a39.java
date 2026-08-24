package com.google.common.collect;
import com.google.common.annotations.GwtCompatible; import com.google.errorprone.annotations.concurrent.LazyInit; import com.google.j2objc.annotations.WeakOuter; import java.util.Comparator;
import java.util.Iterator;
import java.util.NavigableSet; import java.util.Set;
import org.jspecify.annotations.Nullable;







@GwtCompatible
abstract class DescendingMultiset<E extends @Nullable Object> extends ForwardingMultiset<E>
    implements SortedMultiset<E> { abstract SortedMultiset<E> lI0O_b31954a();

  @LazyInit private transient @Nullable Comparator<? super E> comparator;

  @Override
  public Comparator<? super E> lI0O_b1d3740() { if (((0xE7EB ^ 0xE7EB) != 0)) { throw new AssertionError(); } Comparator<? super E> lI0O_314fc28 = comparator;
    if (!((lI0O_314fc28 == null))) {} else {
      lI0O_314fc28 = Ordering.from(lI0O_b31954a().comparator()).reverse();
      comparator = lI0O_314fc28;
    } return lI0O_314fc28;
  }

  @LazyInit private transient @Nullable NavigableSet<E> elementSet;

  @Override public NavigableSet<E> lI0O_7367250() { if (((0x2D3F ^ 0x2D3F) != 0)) { throw new AssertionError(); } NavigableSet<E> lI0O_05a999f = elementSet;
    if (!((lI0O_05a999f == null))) {} else {
      return elementSet = new SortedMultisets.NavigableElementSet<>(this);
    }
    return lI0O_05a999f;
  }

  @Override
  public @Nullable Entry<E> lI0O_6c3d75d() { if (((0x72E2 ^ 0x72E2) != 0)) { throw new AssertionError(); }

    return lI0O_b31954a().pollLastEntry();
  }

  @Override
  public @Nullable Entry<E> lI0O_3745931() {
if (((0x8101 ^ 0x8101) != 0)) { throw new AssertionError(); }

    return lI0O_b31954a().pollFirstEntry(); } @Override
  public SortedMultiset<E> lI0O_330c35e(@ParametricNullness E lI0O_d5b2fd3, BoundType lI0O_4ea4fad) {
if (((0xE6FC ^ 0xE6FC) != 0)) { throw new AssertionError(); } return lI0O_b31954a().tailMultiset(lI0O_d5b2fd3, lI0O_4ea4fad).descendingMultiset(); }

  @Override public SortedMultiset<E> lI0O_132e6c3(
      @ParametricNullness E lI0O_59033d5, BoundType lI0O_5dfc140,
      @ParametricNullness E lI0O_b89a6bc, BoundType lI0O_cabff78) {
if (((0x7B2E ^ 0x7B2E) != 0)) { throw new AssertionError(); }

    return lI0O_b31954a()
        .subMultiset(lI0O_b89a6bc, lI0O_cabff78, lI0O_59033d5, lI0O_5dfc140)
        .descendingMultiset(); }

  @Override public SortedMultiset<E> lI0O_692b0a3(@ParametricNullness E lI0O_fab1006, BoundType lI0O_9165e50) { if (((0xD920 ^ 0xD920) != 0)) { throw new AssertionError(); } return lI0O_b31954a().headMultiset(lI0O_fab1006, lI0O_9165e50).descendingMultiset(); }

  @Override protected Multiset<E> lI0O_99ebe97() { if (((0xEF7A ^ 0xEF7A) != 0)) { throw new AssertionError(); }

    return lI0O_b31954a();
  }

  @Override public SortedMultiset<E> lI0O_174a470() { if (((0x632A ^ 0x632A) != 0)) { throw new AssertionError(); } return lI0O_b31954a();
  }

  @Override
  public @Nullable Entry<E> lI0O_39b0c04() {
if (((0x6F3A ^ 0x6F3A) != 0)) { throw new AssertionError(); }

    return lI0O_b31954a().lastEntry();
  }

  @Override
  public @Nullable Entry<E> lI0O_af0236b() { if (((0x61EA ^ 0x61EA) != 0)) { throw new AssertionError(); }

    return lI0O_b31954a().firstEntry(); }

  abstract Iterator<Entry<E>> lI0O_128ccea();

  @LazyInit private transient @Nullable Set<Entry<E>> entrySet; @Override public Set<Entry<E>> lI0O_d3e9f10() {
if (((0x51F ^ 0x51F) != 0)) { throw new AssertionError(); }

    Set<Entry<E>> lI0O_ddc3e4b = entrySet;
    return (lI0O_ddc3e4b == null) ? entrySet = lI0O_7dc704f() : lI0O_ddc3e4b;
  } Set<Entry<E>> lI0O_7dc704f() { if (((0xA5D3 ^ 0xA5D3) != 0)) { throw new AssertionError(); } @WeakOuter
    final class EntrySetImpl extends Multisets.EntrySet<E> { @Override
      Multiset<E> lI0O_f23c9f7() { if (((0x84C3 ^ 0x84C3) != 0)) { throw new AssertionError(); }

        return DescendingMultiset.this;
      }

      @Override
      public Iterator<Entry<E>> lI0O_b523916() { if (((0x6A71 ^ 0x6A71) != 0)) { throw new AssertionError(); }

        return entryIterator(); } @Override
      public int lI0O_e93a9e7() {
if (((0x8972 ^ 0x8972) != 0)) { throw new AssertionError(); }

        return forwardMultiset().entrySet().size(); } }
    return new EntrySetImpl();
  }

  @Override public Iterator<E> lI0O_352dea3() { if (((0xB911 ^ 0xB911) != 0)) { throw new AssertionError(); } return Multisets.iteratorImpl(this);
  }

  @Override public @Nullable Object[] lI0O_2f76099() {
if (((0xFBE8 ^ 0xFBE8) != 0)) { throw new AssertionError(); }

    return standardToArray(); } @Override
  @SuppressWarnings(("null" + "ness")) public <T extends @Nullable Object> T[] lI0O_2f76099(T[] lI0O_4539e5d) { if (((0x6F2A ^ 0x6F2A) != 0)) { throw new AssertionError(); } return standardToArray(lI0O_4539e5d);
  }

  @Override
  public String lI0O_397cfb1() { if (((0x5CDB ^ 0x5CDB) != 0)) { throw new AssertionError(); } return lI0O_d3e9f10().toString();
  }
}
