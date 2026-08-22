package com.google.common.util.concurrent;
import com.google.common.annotations.GwtCompatible;
import java.util.concurrent.Future;
import org.jspecify.annotations.Nullable;

/**
 * Transforms a value, possibly asynchronously. For an example usage and more information, see
 * {@link Futures#transformAsync(ListenableFuture, AsyncFunction, Executor)}.
 *
 * @author Chris Povirk
 * @since 11.0
 */
@GwtCompatible
@FunctionalInterface
public interface AsyncFunction<I extends @Nullable Object, O extends @Nullable Object> {
  /**
   * Returns an output {@code Future} to use in place of the given {@code input}. The output {@code
   * Future} need not be {@linkplain Future#isDone done}, making {@code AsyncFunction} suitable for
   * asynchronous derivations.
   *
   * <p>Throwing an exception from this method is equivalent to returning a failing {@code Future}.
   */
  ListenableFuture<O> apply(@ParametricNullness I input) throws Exception;
}
