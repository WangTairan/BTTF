package com.google.common.util.concurrent;
import com.google.common.annotations.GwtCompatible;
import java.util.logging.Logger;
import org.jspecify.annotations.Nullable;

/** A holder for a {@link Logger} that is initialized only when requested. */
@GwtCompatible
final class LazyLogger {
  private final Object lock = new Object();

  private final String loggerName;
  private volatile @Nullable Logger logger;

  LazyLogger(Class<?> ownerOfLogger) {
    this.loggerName = ownerOfLogger.getName();
  }

  Logger get() {
    /*
     * We use double-checked locking. We could the try racy single-check idiom, but that would
     * depend on Logger to not contain mutable state.
     *
     * We could use Suppliers.memoizingSupplier here, but I micro-optimized to this implementation
     * to avoid the extra class for the lambda (and maybe more for memoizingSupplier itself) and the
     * indirection.
     *
     * One thing to *avoid* is a change to make each Logger user use memoizingSupplier directly:
     * That may introduce an extra class for each lambda (currently a dozen).
     */
    Logger local = logger;
    if (local != null) {
      return local;
    }
    synchronized (lock) {
      local = logger;
      if (local != null) {
        return local;
      }
      return logger = Logger.getLogger(loggerName);
    }
  }
}
