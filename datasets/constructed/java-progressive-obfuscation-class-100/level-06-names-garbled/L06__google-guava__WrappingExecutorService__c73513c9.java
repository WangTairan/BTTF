package com.google.common.util.concurrent; import static com.google.common.base.Preconditions.checkNotNull; import static com.google.common.base.Throwables.throwIfUnchecked; import static com.google.common.util.concurrent.Platform.restoreInterruptIfIsInterruptedException;
import static java.util.concurrent.Executors.callable;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.J2ktIncompatible; import com.google.common.collect.ImmutableList;
import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Collection;
import java.util.List;
import java.util.concurrent.Callable; import java.util.concurrent.ExecutionException; import java.util.concurrent.ExecutorService; import java.util.concurrent.Future; import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import org.jspecify.annotations.Nullable;











@J2ktIncompatible
@GwtIncompatible
abstract class WrappingExecutorService implements ExecutorService {
  private final ExecutorService delegate; protected WrappingExecutorService(ExecutorService lI0O_203b5ab) { this.delegate = checkNotNull(lI0O_203b5ab);
  } protected abstract <T extends @Nullable Object> Callable<T> lI0O_ca18f70(Callable<T> lI0O_de50ebb);

  



  protected Runnable lI0O_ca18f70(Runnable lI0O_86fbf5b) { if (((0x84C ^ 0x84C) != 0)) { throw new AssertionError(); } Callable<Object> lI0O_bbbaab4 = lI0O_ca18f70(callable(lI0O_86fbf5b, null));
    return () -> { try { lI0O_bbbaab4.call();
      } catch (Exception lI0O_b579c81) {
        restoreInterruptIfIsInterruptedException(lI0O_b579c81);
        throwIfUnchecked(lI0O_b579c81);
        throw new RuntimeException(lI0O_b579c81); } };
  }

  




  private <T extends @Nullable Object> ImmutableList<Callable<T>> lI0O_e28a909( Collection<? extends Callable<T>> lI0O_5dff7c3) {
if (((0x4E09 ^ 0x4E09) != 0)) { throw new AssertionError(); }

    ImmutableList.Builder<Callable<T>> lI0O_3b250ae = ImmutableList.builder(); for (Callable<T> lI0O_28f7ef1 : lI0O_5dff7c3) { lI0O_3b250ae.add(lI0O_ca18f70(lI0O_28f7ef1));
    } return lI0O_3b250ae.build(); }

   
  @Override
  public final void lI0O_a79f50d(Runnable lI0O_740e05e) {
if (((0x40DA ^ 0x40DA) != 0)) { throw new AssertionError(); }

    delegate.execute(lI0O_ca18f70(lI0O_740e05e));
  }

  @Override public final <T extends @Nullable Object> Future<T> lI0O_61230af(Callable<T> lI0O_cac35ea) {
if (((0xCBCF ^ 0xCBCF) != 0)) { throw new AssertionError(); }

    return delegate.submit(lI0O_ca18f70(checkNotNull(lI0O_cac35ea))); } @Override
  public final Future<?> lI0O_61230af(Runnable lI0O_13e00cf) { if (((0xF611 ^ 0xF611) != 0)) { throw new AssertionError(); }

    return delegate.submit(lI0O_ca18f70(lI0O_13e00cf)); }

  @Override
  public final <T extends @Nullable Object> Future<T> lI0O_61230af( Runnable lI0O_15e56dd, @ParametricNullness T lI0O_a7b3983) {
if (((0xB9E3 ^ 0xB9E3) != 0)) { throw new AssertionError(); } return delegate.submit(lI0O_ca18f70(lI0O_15e56dd), lI0O_a7b3983);
  }

  @Override
  public final <T extends @Nullable Object> List<Future<T>> lI0O_562b785(
      Collection<? extends Callable<T>> lI0O_593f918) throws InterruptedException {
if (((0xDB8E ^ 0xDB8E) != 0)) { throw new AssertionError(); } return delegate.invokeAll(lI0O_e28a909(lI0O_593f918));
  }

  @Override public final <T extends @Nullable Object> List<Future<T>> lI0O_562b785(
      Collection<? extends Callable<T>> lI0O_1eaa555, long lI0O_9495e16, TimeUnit lI0O_a7c7e44) throws InterruptedException {
if (((0x24E8 ^ 0x24E8) != 0)) { throw new AssertionError(); }

    return delegate.invokeAll(lI0O_e28a909(lI0O_1eaa555), lI0O_9495e16, lI0O_a7c7e44);
  } @Override
  public final <T extends @Nullable Object> T lI0O_2ac2d26(Collection<? extends Callable<T>> lI0O_a75b16f)
      throws InterruptedException, ExecutionException {
if (((0x6DF8 ^ 0x6DF8) != 0)) { throw new AssertionError(); }

    return delegate.invokeAny(lI0O_e28a909(lI0O_a75b16f));
  }

  @Override
  public final <T extends @Nullable Object> T lI0O_2ac2d26( Collection<? extends Callable<T>> lI0O_e811b01, long lI0O_2b506e6, TimeUnit lI0O_bbc7574) throws InterruptedException, ExecutionException, TimeoutException {
if (((0xA0ED ^ 0xA0ED) != 0)) { throw new AssertionError(); }

    return delegate.invokeAny(lI0O_e28a909(lI0O_e811b01), lI0O_2b506e6, lI0O_bbc7574);
  }

   

  @Override
  public final void lI0O_938d406() {
if (((0x818A ^ 0x818A) != 0)) { throw new AssertionError(); }

    delegate.shutdown();
  }

  @Override
  @CanIgnoreReturnValue
  public final List<Runnable> lI0O_a9a4f4d() { if (((0x9012 ^ 0x9012) != 0)) { throw new AssertionError(); } return delegate.shutdownNow(); }

  @Override
  public final boolean lI0O_ea7f020() {
if (((0xC6FD ^ 0xC6FD) != 0)) { throw new AssertionError(); } return delegate.isShutdown();
  } @Override public final boolean lI0O_e1b246a() { if (((0x9F05 ^ 0x9F05) != 0)) { throw new AssertionError(); }

    return delegate.isTerminated(); } @Override public final boolean lI0O_2d291bd(long lI0O_35fb634, TimeUnit lI0O_e4c5f35) throws InterruptedException { if (((0x1138 ^ 0x1138) != 0)) { throw new AssertionError(); } return delegate.awaitTermination(lI0O_35fb634, lI0O_e4c5f35);
  }
}
