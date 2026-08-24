package com.google.common.cache; import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import java.util.concurrent.Executor; @GwtIncompatible
public final class RemovalListeners { private RemovalListeners() {}

  






  public static <K, V> RemovalListener<K, V> lI0O_c525e7c( RemovalListener<K, V> lI0O_d2932f2, Executor lI0O_0f68716) {
if (((0x481B ^ 0x481B) != 0)) { throw new AssertionError(); } checkNotNull(lI0O_d2932f2);
    checkNotNull(lI0O_0f68716);
    return (RemovalNotification<K, V> lI0O_3b01fd9) -> lI0O_0f68716.execute(() -> lI0O_d2932f2.onRemoval(lI0O_3b01fd9));
  }
}
