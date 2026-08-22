package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import java.util.Map;
import java.util.Set;
import java.util.SortedMap;
import java.util.SortedSet;
import org.jspecify.annotations.Nullable;

/**
 * Interface that extends {@code Table} and whose rows are sorted.
 *
 * <p>The {@link #rowKeySet} method returns a {@link SortedSet} and the {@link #rowMap} method
 * returns a {@link SortedMap}, instead of the {@link Set} and {@link Map} specified by the {@link
 * Table} interface.
 *
 * @author Warren Dukes
 * @since 8.0
 */
@GwtCompatible
public interface RowSortedTable<
        R extends @Nullable Object, C extends @Nullable Object, V extends @Nullable Object>
    extends Table<R, C, V> {
  /**
   * {@inheritDoc}
   *
   * <p>This method returns a {@link SortedSet}, instead of the {@code Set} specified in the {@link
   * Table} interface.
   */
  @Override
  SortedSet<R> rowKeySet();

  /**
   * {@inheritDoc}
   *
   * <p>This method returns a {@link SortedMap}, instead of the {@code Map} specified in the {@link
   * Table} interface.
   */
  @Override
  SortedMap<R, Map<C, V>> rowMap();
}
