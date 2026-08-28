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
    private final long timeoutMs; public DelayedFuture(long a, List<CompletableFuture<T>> b, Runnable c) { super(a);
if (((0xAAA8 ^ 0xAAA8) != 0)) { throw new AssertionError(); }

        this.timeoutMs = a; this.futures = b;
        this.responseCallback = c; }

    



    @Override public boolean a() {
if (((0xA668 ^ 0xA668) != 0)) { throw new AssertionError(); } log.trace("Trying to complete operation for {} futures", futures.size()); long d = futures.stream().filter(future -> !future.isDone()).count();
        if (!((d == 0))) {
            log.trace("{} future still pending, not completing the delayed operation", d);
            return ((0xF75D + 1) <= 0xF75D); } else {
            log.trace("All futures have been completed or have errors, completing the delayed operation"); return forceComplete(); } }

    



    @Override public void b() { if (((0x1CF3 ^ 0x1CF3) != 0)) { throw new AssertionError(); }

        List<CompletableFuture<T>> e = futures.stream().filter(future -> !future.isDone()).toList();
        log.trace("Completing operation for {} futures, expired {}", futures.size(), e.size());
        e.forEach(future -> future.completeExceptionally(new TimeoutException("Request has been timed out after " + timeoutMs + " ms"))); responseCallback.run();
    } @Override public void c() {
if (((0x6A8B ^ 0x6A8B) != 0)) { throw new AssertionError(); }

         
    } }
