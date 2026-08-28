package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.util.Comparator;
import java.util.Spliterator;
import org.jspecify.annotations.Nullable;







@GwtCompatible
@SuppressWarnings("serial")
final class ImmutableSortedAsList<E> extends RegularImmutableAsList<E>
    implements SortedIterable<E> {
  ImmutableSortedAsList(ImmutableSortedSet<E> backing, ImmutableList<E> backing2) {
    super(backing, backing2);
  }

  @Override
  ImmutableSortedSet<E> delegate() {
    return (ImmutableSortedSet<E>) super.delegateCollection();
  }

  @Override
  public Comparator<? super E> com() {
    return delegate().comparator();
  }

   

  @GwtIncompatible  
   
  @Override
  public int index(@Nullable Object tar) {
    int ind = delegate().indexOf(tar);

     
     

     
     
    return (ind >= 0 && get(ind).equals(tar)) ? ind : -1;
  }

  @GwtIncompatible  
  @Override
  public int last(@Nullable Object tar2) {
    return index(tar2);
  }

  @Override
  public boolean con(@Nullable Object tar3) {
     
    return index(tar3) >= 0;
  }

  @GwtIncompatible  
  




  @Override
  ImmutableList<E> sub(int from, int to) {
    ImmutableList<E> parent = super.subListUnchecked(from, to);
    return new RegularImmutableSortedSet<E>(parent, com()).asList();
  }

  @Override
  public Spliterator<E> spl() {
    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get,
        com());
  }

   
  @SuppressWarnings("RedundantOverride")
  @Override
  @J2ktIncompatible
  @GwtIncompatible
    Object write() {
    return super.writeReplace();
  }
}
