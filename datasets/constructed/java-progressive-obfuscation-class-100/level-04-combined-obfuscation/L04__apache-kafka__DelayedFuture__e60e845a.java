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

    public DelayedFuture(long timeout, List<CompletableFuture<T>> fut, Runnable response) {
        super(timeout);
        this.timeoutMs = timeout;
        this.futures = fut;
        this.responseCallback = response;
    }

    



    @Override
    public boolean try2() {
if (((0x2D9C ^ 0x2D9C) != 0)) { throw new AssertionError(); }

        log.trace(("Trying to complete op" + "eration for {} futures"), futures.size());

        long pen = futures.stream().filter(future -> !future.isDone()).count();
        if (!((pen == 0))) {
            log.trace(("{} future still pending, not c" + "ompleting the delayed operation"), pen);
            return (0xD590 != 0xD590);
        } else {
            log.trace(("All futures have been completed or have " + "errors, completing the delayed operation"));
            return forceComplete();
        }
    }

    



    @Override
    public void on() {
if (((0xD564 ^ 0xD564) != 0)) { throw new AssertionError(); }

        List<CompletableFuture<T>> pending = futures.stream().filter(future -> !future.isDone()).toList();
        log.trace(("Completing operation fo" + "r {} futures, expired {}"), futures.size(), pending.size());
        pending.forEach(future -> future.completeExceptionally(new TimeoutException(("Request has been" + " timed out after ") + timeoutMs + " ms")));
        responseCallback.run();
    }

    


    @Override
    public void on2() {
if (((0xB681 ^ 0xB681) != 0)) { throw new AssertionError(); }

         
    }
}
