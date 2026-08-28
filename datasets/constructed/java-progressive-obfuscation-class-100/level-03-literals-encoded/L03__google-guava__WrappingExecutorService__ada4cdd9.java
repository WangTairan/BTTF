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











@J2ktIncompatible
@GwtIncompatible
abstract class WrappingExecutorService implements ExecutorService {
  private final ExecutorService delegate;

  protected WrappingExecutorService(ExecutorService del) {
    this.delegate = checkNotNull(del);
  }

  



  protected abstract <T extends @Nullable Object> Callable<T> wrap(Callable<T> cal);

  



  protected Runnable wrap(Runnable com2) {
    Callable<Object> wra = wrap(callable(com2, null));
    return () -> {
      try {
        wra.call();
      } catch (Exception e) {
        restoreInterruptIfIsInterruptedException(e);
        throwIfUnchecked(e);
        throw new RuntimeException(e);
      }
    };
  }

  




  private <T extends @Nullable Object> ImmutableList<Callable<T>> wrap2(
      Collection<? extends Callable<T>> tas) {
    ImmutableList.Builder<Callable<T>> bui = ImmutableList.builder();
    for (Callable<T> tas2 : tas) {
      bui.add(wrap(tas2));
    }
    return bui.build();
  }

   
  @Override
  public final void exe(Runnable com3) {
    delegate.execute(wrap(com3));
  }

  @Override
  public final <T extends @Nullable Object> Future<T> sub(Callable<T> tas3) {
    return delegate.submit(wrap(checkNotNull(tas3)));
  }

  @Override
  public final Future<?> sub(Runnable tas4) {
    return delegate.submit(wrap(tas4));
  }

  @Override
  public final <T extends @Nullable Object> Future<T> sub(
      Runnable tas5, @ParametricNullness T res) {
    return delegate.submit(wrap(tas5), res);
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> invoke(
      Collection<? extends Callable<T>> tas6) throws InterruptedException {
    return delegate.invokeAll(wrap2(tas6));
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> invoke(
      Collection<? extends Callable<T>> tas7, long tim, TimeUnit uni)
      throws InterruptedException {
    return delegate.invokeAll(wrap2(tas7), tim, uni);
  }

  @Override
  public final <T extends @Nullable Object> T invoke2(Collection<? extends Callable<T>> tas8)
      throws InterruptedException, ExecutionException {
    return delegate.invokeAny(wrap2(tas8));
  }

  @Override
  public final <T extends @Nullable Object> T invoke2(
      Collection<? extends Callable<T>> tas9, long tim2, TimeUnit uni2)
      throws InterruptedException, ExecutionException, TimeoutException {
    return delegate.invokeAny(wrap2(tas9), tim2, uni2);
  }

   

  @Override
  public final void shu() {
    delegate.shutdown();
  }

  @Override
  @CanIgnoreReturnValue
  public final List<Runnable> shutdown() {
    return delegate.shutdownNow();
  }

  @Override
  public final boolean is() {
    return delegate.isShutdown();
  }

  @Override
  public final boolean is2() {
    return delegate.isTerminated();
  }

  @Override
  public final boolean await(long tim3, TimeUnit uni3) throws InterruptedException {
    return delegate.awaitTermination(tim3, uni3);
  }
}
