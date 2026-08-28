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
  ImmutableSortedAsList(ImmutableSortedSet<E> backingSet, ImmutableList<E> backingList) {
    super(backingSet, backingList);
  }

  @Override
  ImmutableSortedSet<E> delegateCollection() {
    return (ImmutableSortedSet<E>) super.delegateCollection();
  }

  @Override
  public Comparator<? super E> comparator() {
    return delegateCollection().comparator();
  }

   

  @GwtIncompatible  
   
  @Override
  public int indexOf(@Nullable Object target) {
    int index = delegateCollection().indexOf(target);

     
     

     
     
    return (index >= 0 && get(index).equals(target)) ? index : -1;
  }

  @GwtIncompatible  
  @Override
  public int lastIndexOf(@Nullable Object target) {
    return indexOf(target);
  }

  @Override
  public boolean contains(@Nullable Object target) {
     
    return indexOf(target) >= 0;
  }

  @GwtIncompatible  
  




  @Override
  ImmutableList<E> subListUnchecked(int fromIndex, int toIndex) {
    ImmutableList<E> parentSubList = super.subListUnchecked(fromIndex, toIndex);
    return new RegularImmutableSortedSet<E>(parentSubList, comparator()).asList();
  }

  @Override
  public Spliterator<E> spliterator() {
    return CollectSpliterators.indexed(
        size(),
        ImmutableList.SPLITERATOR_CHARACTERISTICS | Spliterator.SORTED | Spliterator.DISTINCT,
        delegateList()::get,
        comparator());
  }

   
  @SuppressWarnings("RedundantOverride")
  @Override
  @J2ktIncompatible
  @GwtIncompatible
    Object writeReplace() {
    return super.writeReplace();
  }
}
