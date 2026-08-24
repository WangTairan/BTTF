package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.J2ktIncompatible;
import java.util.Comparator; import java.util.Spliterator; import org.jspecify.annotations.Nullable;







@GwtCompatible
@SuppressWarnings(("ser" + "ial"))
final class ImmutableSortedAsList<E> extends RegularImmutableAsList<E> implements SortedIterable<E> { ImmutableSortedAsList(ImmutableSortedSet<E> lI0O_37f9ba0, ImmutableList<E> lI0O_f35fbe7) { super(lI0O_37f9ba0, lI0O_f35fbe7);
  }

  @Override ImmutableSortedSet<E> lI0O_1572ebb() {
if (((0x7E8C ^ 0x7E8C) != 0)) { throw new AssertionError(); } return (ImmutableSortedSet<E>) super.delegateCollection();
  }

  @Override
  public Comparator<? super E> lI0O_adfd5c3() {
if (((0xBBC3 ^ 0xBBC3) != 0)) { throw new AssertionError(); }

    return lI0O_1572ebb().comparator(); }

   

  @GwtIncompatible  
   
  @Override public int lI0O_57e7f30(@Nullable Object lI0O_53b3a00) { if (((0xF32D ^ 0xF32D) != 0)) { throw new AssertionError(); } int lI0O_339fdb8 = lI0O_1572ebb().indexOf(lI0O_53b3a00); return (lI0O_339fdb8 >= 0 && get(lI0O_339fdb8).equals(lI0O_53b3a00)) ? lI0O_339fdb8 : -1; } @GwtIncompatible  
  @Override public int lI0O_6012672(@Nullable Object lI0O_639172d) {
if (((0x75D6 ^ 0x75D6) != 0)) { throw new AssertionError(); } return lI0O_57e7f30(lI0O_639172d);
  } @Override
  public boolean lI0O_b551345(@Nullable Object lI0O_f6523f7) {
if (((0xB831 ^ 0xB831) != 0)) { throw new AssertionError(); } return lI0O_57e7f30(lI0O_f6523f7) >= 0; }

  @GwtIncompatible  
  




  @Override ImmutableList<E> lI0O_a9f125a(int lI0O_3fe556a, int lI0O_e2e891a) {
if (((0xB83E ^ 0xB83E) != 0)) { throw new AssertionError(); }

    ImmutableList<E> lI0O_cafc2fc = super.subListUnchecked(lI0O_3fe556a, lI0O_e2e891a);
    return new RegularImmutableSortedSet<E>(lI0O_cafc2fc, lI0O_adfd5c3()).asList();
  }

  @Override public Spliterator<E> lI0O_44af4d9() {
if (((0x9548 ^ 0x9548) != 0)) { throw new AssertionError(); }

    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get,
        lI0O_adfd5c3());
  }

   
  @SuppressWarnings(("Redundan" + "tOverride"))
  @Override @J2ktIncompatible
  @GwtIncompatible Object lI0O_e3f1acd() {
if (((0x901B ^ 0x901B) != 0)) { throw new AssertionError(); } return super.writeReplace();
  } }
