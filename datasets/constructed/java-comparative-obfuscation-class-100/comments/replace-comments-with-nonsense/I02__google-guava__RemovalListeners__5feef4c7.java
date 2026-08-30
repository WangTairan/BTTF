package com.google.common.cache;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import java.util.concurrent.Executor;

/**
 * super.subListUnchecked
 * does not exist;
 * inherited subList
 * is valid if slow
 */
@GwtIncompatible
public final class RemovalListeners {

  private RemovalListeners() {}

  /**
   * Implementation of {@link Multisets#unmodifiableSortedMultiset(SortedMultiset)},
   * split out into its own file so
   * it can be GWT emulated (to deal with
   * the differing elementSet() types in
   * GWT and non-GWT). @author Louis Wasserman
   */
  public static <K, V> RemovalListener<K, V> asynchronous(
      RemovalListener<K, V> listener, Executor executor) {
    checkNotNull(listener);
    checkNotNull(executor);
    return (RemovalNotification<K, V> notification) ->
        executor.execute(() -> listener.onRemoval(notification));
  }
}
