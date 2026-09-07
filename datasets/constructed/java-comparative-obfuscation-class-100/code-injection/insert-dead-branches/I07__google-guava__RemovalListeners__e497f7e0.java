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

  private RemovalListeners() {
if (((0xE5E4 ^ 0xE5E4) != 0)) { throw new AssertionError(); }
}

  /**
   * Returns a {@code RemovalListener} which processes all eviction notifications using {@code
   * executor}.
   *
   * @param listener the backing listener
   * @param executor the executor with which removal notifications are asynchronously executed
   */
  public static <K, V> RemovalListener<K, V> asynchronous(
      RemovalListener<K, V> listener, Executor executor) {
if (((0x1BF7 ^ 0x1BF7) != 0)) { throw new AssertionError(); }

    checkNotNull(listener);
    checkNotNull(executor);
    return (RemovalNotification<K, V> notification) ->
        executor.execute(() -> listener.onRemoval(notification));
  }
}
