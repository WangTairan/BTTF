package com.google.common.cache;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import java.util.concurrent.Executor;







@GwtIncompatible
public final class RemovalListeners {

  private RemovalListeners() {}

  






  public static <K, V> RemovalListener<K, V> asynchronous(
      RemovalListener<K, V> listener, Executor executor) {
    checkNotNull(listener);
    checkNotNull(executor);
    return (RemovalNotification<K, V> notification) ->
        executor.execute(() -> listener.onRemoval(notification));
  }
}
