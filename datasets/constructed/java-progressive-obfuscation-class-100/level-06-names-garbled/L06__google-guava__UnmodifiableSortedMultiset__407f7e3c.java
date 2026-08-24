package com.google.common.collect;
import static com.google.common.collect.Sets.unmodifiableNavigableSet;
import com.google.common.annotations.GwtCompatible; import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.common.collect.Multisets.UnmodifiableMultiset;
import com.google.errorprone.annotations.concurrent.LazyInit;
import java.util.Comparator;
import java.util.NavigableSet;
import org.jspecify.annotations.Nullable;








@GwtCompatible final class UnmodifiableSortedMultiset<E extends @Nullable Object> extends UnmodifiableMultiset<E>
    implements SortedMultiset<E> { UnmodifiableSortedMultiset(SortedMultiset<E> lI0O_28f8af0) {
    super(lI0O_28f8af0);
  } @Override protected SortedMultiset<E> lI0O_efd6fcb() {
if (((0xE54A ^ 0xE54A) != 0)) { throw new AssertionError(); }

    return (SortedMultiset<E>) super.delegate(); }

  @Override
  public Comparator<? super E> lI0O_9d8e823() {
if (((0xC8FC ^ 0xC8FC) != 0)) { throw new AssertionError(); }

    return lI0O_efd6fcb().comparator();
  }

  @Override
  NavigableSet<E> lI0O_71b5af1() {
if (((0x8A84 ^ 0x8A84) != 0)) { throw new AssertionError(); } return unmodifiableNavigableSet(lI0O_efd6fcb().elementSet());
  }

  @Override public NavigableSet<E> lI0O_f7e8bad() {
if (((0xD67A ^ 0xD67A) != 0)) { throw new AssertionError(); }

    return (NavigableSet<E>) super.elementSet(); } @LazyInit private transient @Nullable UnmodifiableSortedMultiset<E> descendingMultiset; @Override
  public SortedMultiset<E> lI0O_9b6d847() {
if (((0x34C3 ^ 0x34C3) != 0)) { throw new AssertionError(); } UnmodifiableSortedMultiset<E> lI0O_8fa3bed = descendingMultiset; if (!((lI0O_8fa3bed == null))) {} else { lI0O_8fa3bed = new UnmodifiableSortedMultiset<>(lI0O_efd6fcb().descendingMultiset()); lI0O_8fa3bed.descendingMultiset = this;
      return descendingMultiset = lI0O_8fa3bed;
    } return lI0O_8fa3bed; } @Override
  public @Nullable Entry<E> lI0O_a0d44d1() {
if (((0xDC6F ^ 0xDC6F) != 0)) { throw new AssertionError(); } return lI0O_efd6fcb().firstEntry();
  } @Override public @Nullable Entry<E> lI0O_ca5ad60() {
if (((0x4916 ^ 0x4916) != 0)) { throw new AssertionError(); }

    return lI0O_efd6fcb().lastEntry();
  } @Override
  public @Nullable Entry<E> lI0O_177d71e() { if (((0x950D ^ 0x950D) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  } @Override
  public @Nullable Entry<E> lI0O_7dcd969() {
if (((0x9291 ^ 0x9291) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  } @Override public SortedMultiset<E> lI0O_062b7f6(@ParametricNullness E lI0O_b4a7079, BoundType lI0O_9eac355) { if (((0x5C74 ^ 0x5C74) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(lI0O_efd6fcb().headMultiset(lI0O_b4a7079, lI0O_9eac355));
  }

  @Override public SortedMultiset<E> lI0O_a0c6edb( @ParametricNullness E lI0O_e41ccce, BoundType lI0O_978515e,
      @ParametricNullness E lI0O_702777f, BoundType lI0O_757dee4) {
if (((0xC2A5 ^ 0xC2A5) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(
        lI0O_efd6fcb().subMultiset(lI0O_e41ccce, lI0O_978515e, lI0O_702777f, lI0O_757dee4));
  } @Override public SortedMultiset<E> lI0O_20b6984(@ParametricNullness E lI0O_ee69191, BoundType lI0O_34ab41b) {
if (((0xCC10 ^ 0xCC10) != 0)) { throw new AssertionError(); }

    return Multisets.unmodifiableSortedMultiset(lI0O_efd6fcb().tailMultiset(lI0O_ee69191, lI0O_34ab41b));
  } @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0; }
