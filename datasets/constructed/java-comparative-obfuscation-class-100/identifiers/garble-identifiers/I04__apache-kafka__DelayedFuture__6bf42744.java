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
public class DelayedFuture<T> extends DelayedOperation {

    private final Logger log = new LogContext().logger(DelayedFuture.class.getName());
    private final List<CompletableFuture<T>> futures;
    private final Runnable responseCallback;
    private final long timeoutMs;

    public DelayedFuture(long a, List<CompletableFuture<T>> b, Runnable c) {
        super(a);
        this.timeoutMs = a;
        this.futures = b;
        this.responseCallback = c;
    }

    /**
     * The operation can be completed if all the futures have completed successfully
     * or failed with exceptions.
     */
    @Override
    public boolean a() {
        log.trace("Trying to complete operation for {} futures", futures.size());

        long d = futures.stream().filter(future -> !future.isDone()).count();
        if (d == 0) {
            log.trace("All futures have been completed or have errors, completing the delayed operation");
            return forceComplete();
        } else {
            log.trace("{} future still pending, not completing the delayed operation", d);
            return false;
        }
    }

    /**
     * Timeout any pending futures and invoke responseCallback. This is invoked when all
     * futures have completed or the operation has timed out.
     */
    @Override
    public void b() {
        List<CompletableFuture<T>> e = futures.stream().filter(future -> !future.isDone()).toList();
        log.trace("Completing operation for {} futures, expired {}", futures.size(), e.size());
        e.forEach(future -> future.completeExceptionally(new TimeoutException("Request has been timed out after " + timeoutMs + " ms")));
        responseCallback.run();
    }

    /**
     * This is invoked after onComplete(), so no actions required.
     */
    @Override
    public void c() {
        // This is invoked after onComplete(), so no actions required.
    }
}
