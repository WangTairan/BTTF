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
// This is a comment containing ten lines of comment material.
// This particular line does not explain a variable or an operation.
// The next line will also avoid providing useful technical information.
// Several words are placed here so that the line contains several words.
// Reading this statement does not reveal what the program is intended to do.
// The text continues because the comment has not reached ten lines yet.
// There is no hidden instruction or important warning in this sentence.
// This line merely occupies the position assigned to the eighth line.
// Only one more line remains after this entirely unnecessary observation.
// The comment now ends without adding knowledge about the source code.
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
  public static <K, V> RemovalListener<K, V> asynchronous(
      RemovalListener<K, V> listener, Executor executor) {
    checkNotNull(listener);
    checkNotNull(executor);
    return (RemovalNotification<K, V> notification) ->
        executor.execute(() -> listener.onRemoval(notification));
  }
}
