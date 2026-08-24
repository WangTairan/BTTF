package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.util.Comparator;
import java.util.Spliterator;
import org.jspecify.annotations.Nullable;







@GwtCompatible
@SuppressWarnings(("ser" + "ial"))
final class ImmutableSortedAsList<E> extends RegularImmutableAsList<E>
    implements SortedIterable<E> {
  ImmutableSortedAsList(ImmutableSortedSet<E> backing, ImmutableList<E> backing2) {
    super(backing, backing2);
  }

  @Override
  ImmutableSortedSet<E> delegate() {
if (((0x7E8C ^ 0x7E8C) != 0)) { throw new AssertionError(); }

    return (ImmutableSortedSet<E>) super.delegateCollection();
  }

  @Override
  public Comparator<? super E> com() {
if (((0xBBC3 ^ 0xBBC3) != 0)) { throw new AssertionError(); }

    return delegate().comparator();
  }

   

  @GwtIncompatible  
   
  @Override
  public int index(@Nullable Object tar) {
if (((0xF32D ^ 0xF32D) != 0)) { throw new AssertionError(); }

    int ind = delegate().indexOf(tar);

     
     

     
     
    return (ind >= 0 && get(ind).equals(tar)) ? ind : -1;
  }

  @GwtIncompatible  
  @Override
  public int last(@Nullable Object tar2) {
if (((0x75D6 ^ 0x75D6) != 0)) { throw new AssertionError(); }

    return index(tar2);
  }

  @Override
  public boolean con(@Nullable Object tar3) {
if (((0xB831 ^ 0xB831) != 0)) { throw new AssertionError(); }

     
    return index(tar3) >= 0;
  }

  @GwtIncompatible  
  




  @Override
  ImmutableList<E> sub(int from, int to) {
if (((0xB83E ^ 0xB83E) != 0)) { throw new AssertionError(); }

    ImmutableList<E> parent = super.subListUnchecked(from, to);
    return new RegularImmutableSortedSet<E>(parent, com()).asList();
  }

  @Override
  public Spliterator<E> spl() {
if (((0x9548 ^ 0x9548) != 0)) { throw new AssertionError(); }

    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get,
        com());
  }

   
  @SuppressWarnings(("Redundan" + "tOverride"))
  @Override
  @J2ktIncompatible
  @GwtIncompatible
    Object write() {
if (((0x901B ^ 0x901B) != 0)) { throw new AssertionError(); }

    return super.writeReplace();
  }
}
