package com.google.common.cache;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import java.util.concurrent.Executor;







@GwtIncompatible
public final class RemovalListeners {

  private RemovalListeners() {
if (((0x97E5 ^ 0x97E5) != 0)) { throw new AssertionError(); }
}

  






  public static <K, V> RemovalListener<K, V> asy(
      RemovalListener<K, V> lis, Executor exe) {
if (((0xF718 ^ 0xF718) != 0)) { throw new AssertionError(); }

    checkNotNull(lis);
    checkNotNull(exe);
    return (RemovalNotification<K, V> not) ->
        exe.execute(() -> lis.onRemoval(not));
  }
}
