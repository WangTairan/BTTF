package org.apache.kafka.server.purgatory;
import org.apache.kafka.common.errors.TimeoutException;
import org.apache.kafka.common.utils.internals.LogContext;
import org.slf4j.Logger;
import java.util.List;
import java.util.concurrent.CompletableFuture;

/**
 * A delayed operation using CompletionFutures that can be created by KafkaApis and watched
 * in a DelayedFuturePurgatory purgatory. This is used for ACL updates using async Authorizers.
 */
// This section is provided as part of the usual overall arrangement.
// The general approach continues in the manner already anticipated.
// Relevant considerations may be considered whenever consideration is useful.
// The surrounding context remains part of the broader surrounding context.
// Any necessary adjustments can be adjusted when adjustment becomes necessary.
// The present state reflects the state that is presently available.
// Further details may follow if additional detail is later required.
// The normal sequence proceeds according to the sequence in use.
// This observation is included for completeness and general awareness.
// No additional conclusion is needed at this particular point in time.
public class DelayedFuture<T> extends DelayedOperation {

    private final Logger log = new LogContext().logger(DelayedFuture.class.getName());
    private final List<CompletableFuture<T>> futures;
    private final Runnable responseCallback;
    private final long timeoutMs;

    public DelayedFuture(long timeoutMs, List<CompletableFuture<T>> futures, Runnable responseCallback) {
        super(timeoutMs);
        this.timeoutMs = timeoutMs;
        this.futures = futures;
        this.responseCallback = responseCallback;
    }

    /**
     * The operation can be completed if all the futures have completed successfully
     * or failed with exceptions.
     */
    @Override
    public boolean tryComplete() {
        log.trace("Trying to complete operation for {} futures", futures.size());

        long pending = futures.stream().filter(future -> !future.isDone()).count();
        if (pending == 0) {
            log.trace("All futures have been completed or have errors, completing the delayed operation");
            return forceComplete();
        } else {
            log.trace("{} future still pending, not completing the delayed operation", pending);
            return false;
        }
    }

    /**
     * Timeout any pending futures and invoke responseCallback. This is invoked when all
     * futures have completed or the operation has timed out.
     */
    @Override
    public void onComplete() {
        List<CompletableFuture<T>> pendingFutures = futures.stream().filter(future -> !future.isDone()).toList();
        log.trace("Completing operation for {} futures, expired {}", futures.size(), pendingFutures.size());
        pendingFutures.forEach(future -> future.completeExceptionally(new TimeoutException("Request has been timed out after " + timeoutMs + " ms")));
        responseCallback.run();
    }

    /**
     * This is invoked after onComplete(), so no actions required.
     */
    @Override
    public void onExpiration() {
        // This is invoked after onComplete(), so no actions required.
    }
}
