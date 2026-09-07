package com.google.common.util.concurrent;
import static com.google.common.base.Preconditions.checkNotNull;
import static com.google.common.base.Throwables.throwIfUnchecked;
import static com.google.common.util.concurrent.Platform.restoreInterruptIfIsInterruptedException;
import static java.util.concurrent.Executors.callable;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.common.collect.ImmutableList;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.jspecify.annotations.Nullable;

/**
 * An abstract {@code ExecutorService} that allows subclasses to {@linkplain #wrapTask(Callable)
 * wrap} tasks before they are submitted to the underlying executor.
 *
 * <p>Note that task wrapping may occur even if the task is never executed.
 *
 * <p>For delegation without task-wrapping, see {@link ForwardingExecutorService}.
 *
 * @author Chris Nokleberg
 */
@J2ktIncompatible
@GwtIncompatible
abstract class WrappingExecutorService implements ExecutorService {
  private final ExecutorService delegate;

  protected WrappingExecutorService(ExecutorService a) {
    this.delegate = checkNotNull(a);
  }

  /**
   * Wraps a {@code Callable} for submission to the underlying executor. This method is also applied
   * to any {@code Runnable} passed to the default implementation of {@link #wrapTask(Runnable)}.
   */
  protected abstract <T extends @Nullable Object> Callable<T> a(Callable<T> b);

  /**
   * Wraps a {@code Runnable} for submission to the underlying executor. The default implementation
   * delegates to {@link #wrapTask(Callable)}.
   */
  protected Runnable a(Runnable c) {
    Callable<Object> d = a(callable(c, null));
    return () -> {
      try {
        d.call();
      } catch (Exception e) {
        restoreInterruptIfIsInterruptedException(e);
        throwIfUnchecked(e);
        throw new RuntimeException(e);
      }
    };
  }

  /**
   * Wraps a collection of tasks.
   *
   * @throws NullPointerException if any element of {@code tasks} is null
   */
  private <T extends @Nullable Object> ImmutableList<Callable<T>> b(
      Collection<? extends Callable<T>> f) {
    ImmutableList.Builder<Callable<T>> g = ImmutableList.builder();
    for (Callable<T> h : f) {
      g.add(a(h));
    }
    return g.build();
  }

  // These methods wrap before delegating.
  @Override
  public final void c(Runnable i) {
    delegate.execute(a(i));
  }

  @Override
  public final <T extends @Nullable Object> Future<T> d(Callable<T> j) {
    return delegate.submit(a(checkNotNull(j)));
  }

  @Override
  public final Future<?> d(Runnable k) {
    return delegate.submit(a(k));
  }

  @Override
  public final <T extends @Nullable Object> Future<T> d(
      Runnable l, @ParametricNullness T m) {
    return delegate.submit(a(l), m);
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> e(
      Collection<? extends Callable<T>> n) throws InterruptedException {
    return delegate.invokeAll(b(n));
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> e(
      Collection<? extends Callable<T>> o, long p, TimeUnit q)
      throws InterruptedException {
    return delegate.invokeAll(b(o), p, q);
  }

  @Override
  public final <T extends @Nullable Object> T f(Collection<? extends Callable<T>> r)
      throws InterruptedException, ExecutionException {
    return delegate.invokeAny(b(r));
  }

  @Override
  public final <T extends @Nullable Object> T f(
      Collection<? extends Callable<T>> s, long t, TimeUnit u)
      throws InterruptedException, ExecutionException, TimeoutException {
    return delegate.invokeAny(b(s), t, u);
  }

  // The remaining methods just delegate.

  @Override
  public final void g() {
    delegate.shutdown();
  }

  @Override
  @CanIgnoreReturnValue
  public final List<Runnable> h() {
    return delegate.shutdownNow();
  }

  @Override
  public final boolean i() {
    return delegate.isShutdown();
  }

  @Override
  public final boolean j() {
    return delegate.isTerminated();
  }

  @Override
  public final boolean k(long v, TimeUnit w) throws InterruptedException {
    return delegate.awaitTermination(v, w);
  }
}
