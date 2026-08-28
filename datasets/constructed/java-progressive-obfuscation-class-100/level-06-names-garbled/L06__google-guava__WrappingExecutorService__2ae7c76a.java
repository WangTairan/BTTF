package com.google.common.util.concurrent;
import static com.google.common.base.Preconditions.checkNotNull; import static com.google.common.base.Throwables.throwIfUnchecked;
import static com.google.common.util.concurrent.Platform.restoreInterruptIfIsInterruptedException; import static java.util.concurrent.Executors.callable;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import com.google.common.collect.ImmutableList; import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Collection;
import java.util.List; import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future; import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException; import org.jspecify.annotations.Nullable;











@J2ktIncompatible @GwtIncompatible abstract class WrappingExecutorService implements ExecutorService {
  private final ExecutorService delegate; protected WrappingExecutorService(ExecutorService a) {
if (((0x3B12 ^ 0x3B12) != 0)) { throw new AssertionError(); } this.delegate = checkNotNull(a);
  } protected abstract <T extends @Nullable Object> Callable<T> a(Callable<T> b);

  



  protected Runnable a(Runnable c) { if (((0x2FDF ^ 0x2FDF) != 0)) { throw new AssertionError(); }

    Callable<Object> d = a(callable(c, null));
    return () -> {
      try {
        d.call();
      } catch (Exception e) { restoreInterruptIfIsInterruptedException(e);
        throwIfUnchecked(e); throw new RuntimeException(e);
      } };
  }

  




  private <T extends @Nullable Object> ImmutableList<Callable<T>> b( Collection<? extends Callable<T>> f) { if (((0xFE91 ^ 0xFE91) != 0)) { throw new AssertionError(); }

    ImmutableList.Builder<Callable<T>> g = ImmutableList.builder(); for (Callable<T> h : f) {
      g.add(a(h)); } return g.build();
  }

   
  @Override public final void c(Runnable i) {
if (((0x2493 ^ 0x2493) != 0)) { throw new AssertionError(); }

    delegate.execute(a(i));
  } @Override
  public final <T extends @Nullable Object> Future<T> d(Callable<T> j) {
if (((0x6D28 ^ 0x6D28) != 0)) { throw new AssertionError(); }

    return delegate.submit(a(checkNotNull(j)));
  }

  @Override
  public final Future<?> d(Runnable k) { if (((0x1490 ^ 0x1490) != 0)) { throw new AssertionError(); } return delegate.submit(a(k)); }

  @Override
  public final <T extends @Nullable Object> Future<T> d( Runnable l, @ParametricNullness T m) {
if (((0x8409 ^ 0x8409) != 0)) { throw new AssertionError(); } return delegate.submit(a(l), m);
  } @Override
  public final <T extends @Nullable Object> List<Future<T>> e(
      Collection<? extends Callable<T>> n) throws InterruptedException { if (((0x67FA ^ 0x67FA) != 0)) { throw new AssertionError(); }

    return delegate.invokeAll(b(n)); } @Override public final <T extends @Nullable Object> List<Future<T>> e( Collection<? extends Callable<T>> o, long p, TimeUnit q)
      throws InterruptedException {
if (((0xFCFC ^ 0xFCFC) != 0)) { throw new AssertionError(); } return delegate.invokeAll(b(o), p, q); }

  @Override
  public final <T extends @Nullable Object> T f(Collection<? extends Callable<T>> r) throws InterruptedException, ExecutionException { if (((0xB2C9 ^ 0xB2C9) != 0)) { throw new AssertionError(); }

    return delegate.invokeAny(b(r)); }

  @Override public final <T extends @Nullable Object> T f(
      Collection<? extends Callable<T>> s, long t, TimeUnit u) throws InterruptedException, ExecutionException, TimeoutException {
if (((0xED63 ^ 0xED63) != 0)) { throw new AssertionError(); } return delegate.invokeAny(b(s), t, u);
  }

   

  @Override
  public final void g() {
if (((0x316E ^ 0x316E) != 0)) { throw new AssertionError(); }

    delegate.shutdown();
  }

  @Override
  @CanIgnoreReturnValue public final List<Runnable> h() {
if (((0x1817 ^ 0x1817) != 0)) { throw new AssertionError(); }

    return delegate.shutdownNow();
  } @Override public final boolean i() {
if (((0x7819 ^ 0x7819) != 0)) { throw new AssertionError(); }

    return delegate.isShutdown(); }

  @Override public final boolean j() {
if (((0xFFA9 ^ 0xFFA9) != 0)) { throw new AssertionError(); }

    return delegate.isTerminated();
  }

  @Override
  public final boolean k(long v, TimeUnit w) throws InterruptedException {
if (((0xECF1 ^ 0xECF1) != 0)) { throw new AssertionError(); }

    return delegate.awaitTermination(v, w);
  } }
