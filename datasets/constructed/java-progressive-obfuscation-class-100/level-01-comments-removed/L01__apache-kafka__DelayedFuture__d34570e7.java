package org.apache.kafka.server.purgatory;
import org.apache.kafka.common.errors.TimeoutException;
import org.apache.kafka.common.utils.internals.LogContext;
import org.slf4j.Logger;
import java.util.List;
import java.util.concurrent.CompletableFuture;





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

    



    @Override
    public void onComplete() {
        List<CompletableFuture<T>> pendingFutures = futures.stream().filter(future -> !future.isDone()).toList();
        log.trace("Completing operation for {} futures, expired {}", futures.size(), pendingFutures.size());
        pendingFutures.forEach(future -> future.completeExceptionally(new TimeoutException("Request has been timed out after " + timeoutMs + " ms")));
        responseCallback.run();
    }

    


    @Override
    public void onExpiration() {
         
    }
}
