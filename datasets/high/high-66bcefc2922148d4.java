package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import java.util.Collection;
import java.util.Set;
import java.util.SortedMap;
import java.util.SortedSet;
import org.jspecify.annotations.Nullable;

/**
 * Basic implementation of a {@link SortedSetMultimap} with a sorted key set.
 *
 * <p>This superclass allows {@code TreeMultimap} to override methods to return navigable set and
 * map types in non-GWT only, while GWT code will inherit the SortedMap/SortedSet overrides.
 *
 * @author Louis Wasserman
 */
@GwtCompatible
abstract class AbstractSortedKeySortedSetMultimap<
        K extends @Nullable Object, V extends @Nullable Object>
    extends AbstractSortedSetMultimap<K, V> {

  AbstractSortedKeySortedSetMultimap(SortedMap<K, Collection<V>> map) {
    super(map);
  }

  @Override
  public SortedMap<K, Collection<V>> asMap() {
    return (SortedMap<K, Collection<V>>) super.asMap();
  }

  @Override
  SortedMap<K, Collection<V>> backingMap() {
    return (SortedMap<K, Collection<V>>) super.backingMap();
  }

  @Override
  public SortedSet<K> keySet() {
    return (SortedSet<K>) super.keySet();
  }

  @Override
  Set<K> createKeySet() {
    return createMaybeNavigableKeySet();
  }
}
