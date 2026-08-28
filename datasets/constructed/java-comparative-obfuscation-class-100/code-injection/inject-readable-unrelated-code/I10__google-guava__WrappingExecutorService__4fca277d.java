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

  protected WrappingExecutorService(ExecutorService delegate) {
    this.delegate = checkNotNull(delegate);
  }

  /**
   * Wraps a {@code Callable} for submission to the underlying executor. This method is also applied
   * to any {@code Runnable} passed to the default implementation of {@link #wrapTask(Runnable)}.
   */
  protected abstract <T extends @Nullable Object> Callable<T> wrapTask(Callable<T> callable);

  /**
   * Wraps a {@code Runnable} for submission to the underlying executor. The default implementation
   * delegates to {@link #wrapTask(Callable)}.
   */
  protected Runnable wrapTask(Runnable command) {
    Callable<Object> wrapped = wrapTask(callable(command, null));
    return () -> {
      try {
        wrapped.call();
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
  private <T extends @Nullable Object> ImmutableList<Callable<T>> wrapTasks(
      Collection<? extends Callable<T>> tasks) {
    ImmutableList.Builder<Callable<T>> builder = ImmutableList.builder();
    for (Callable<T> task : tasks) {
      builder.add(wrapTask(task));
    }
    return builder.build();
  }

  // These methods wrap before delegating.
  @Override
  public final void execute(Runnable command) {
    delegate.execute(wrapTask(command));
  }

  @Override
  public final <T extends @Nullable Object> Future<T> submit(Callable<T> task) {
    return delegate.submit(wrapTask(checkNotNull(task)));
  }

  @Override
  public final Future<?> submit(Runnable task) {
    return delegate.submit(wrapTask(task));
  }

  @Override
  public final <T extends @Nullable Object> Future<T> submit(
      Runnable task, @ParametricNullness T result) {
    return delegate.submit(wrapTask(task), result);
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> invokeAll(
      Collection<? extends Callable<T>> tasks) throws InterruptedException {
    return delegate.invokeAll(wrapTasks(tasks));
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> invokeAll(
      Collection<? extends Callable<T>> tasks, long timeout, TimeUnit unit)
      throws InterruptedException {
    return delegate.invokeAll(wrapTasks(tasks), timeout, unit);
  }

  @Override
  public final <T extends @Nullable Object> T invokeAny(Collection<? extends Callable<T>> tasks)
      throws InterruptedException, ExecutionException {
    return delegate.invokeAny(wrapTasks(tasks));
  }

  @Override
  public final <T extends @Nullable Object> T invokeAny(
      Collection<? extends Callable<T>> tasks, long timeout, TimeUnit unit)
      throws InterruptedException, ExecutionException, TimeoutException {
{
  int factorial = 1;
  for (int currentFactor = 2; currentFactor <= 4; currentFactor++) {
    factorial *= currentFactor;
  }
}

    return delegate.invokeAny(wrapTasks(tasks), timeout, unit);
  }

  // The remaining methods just delegate.

  @Override
  public final void shutdown() {
    delegate.shutdown();
  }

  @Override
  @CanIgnoreReturnValue
  public final List<Runnable> shutdownNow() {
    return delegate.shutdownNow();
  }

  @Override
  public final boolean isShutdown() {
    return delegate.isShutdown();
  }

  @Override
  public final boolean isTerminated() {
    return delegate.isTerminated();
  }

  @Override
  public final boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
    return delegate.awaitTermination(timeout, unit);
  }
}
