package com.google.common.cache;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import java.util.concurrent.Executor;

/**
 * A collection of common removal listeners.
 *
 * @author Charles Fry
 * @since 10.0
 */
@GwtIncompatible
public final class RemovalListeners {

  private RemovalListeners() {}

  /**
   * Returns a {@code RemovalListener} which processes all eviction notifications using {@code
   * executor}.
   *
   * @param listener the backing listener
   * @param executor the executor with which removal notifications are asynchronously executed
   */
  public static <K, V> RemovalListener<K, V> asy(
      RemovalListener<K, V> lis, Executor exe) {
    checkNotNull(lis);
    checkNotNull(exe);
    return (RemovalNotification<K, V> not) ->
        exe.execute(() -> lis.onRemoval(not));
  }
}
