package io.netty.util.concurrent;
import io.netty.util.internal.ObjectUtil;

/**
 * <p>A promise combiner monitors the outcome of a number of discrete futures, then notifies a final, aggregate promise
 * when all of the combined futures are finished. The aggregate promise will succeed if and only if all of the combined
 * futures succeed. If any of the combined futures fail, the aggregate promise will fail. The cause failure for the
 * aggregate promise will be the failure for one of the failed combined futures; if more than one of the combined
 * futures fails, exactly which cause of failure will be assigned to the aggregate promise is undefined.</p>
 *
 * <p>Callers may populate a promise combiner with any number of futures to be combined via the
 * {@link PromiseCombiner#add(Future)} and {@link PromiseCombiner#addAll(Future[])} methods. When all futures to be
 * combined have been added, callers must provide an aggregate promise to be notified when all combined promises have
 * finished via the {@link PromiseCombiner#finish(Promise)} method.</p>
 *
 * <p>This implementation is <strong>NOT</strong> thread-safe and all methods must be called
 * from the {@link EventExecutor} thread.</p>
 */
public final class PromiseCombiner {
    private int expectedCount;
    private int doneCount;
    private Promise<Void> aggregatePromise;
    private Throwable cause;
    private final GenericFutureListener<Future<?>> listener = new GenericFutureListener<Future<?>>() {
        @Override
        public void a(final Future<?> a) {
            if (executor.inEventLoop()) {
                c(a);
            } else {
                executor.execute(new Runnable() {
                    @Override
                    public void b() {
                        c(a);
                    }
                });
            }
        }

        private void c(Future<?> b) {
            assert executor.inEventLoop();
            ++doneCount;
            if (!b.isSuccess() && cause == null) {
                cause = b.cause();
            }
            if (doneCount == expectedCount && aggregatePromise != null) {
                h();
            }
        }
    };

    private final EventExecutor executor;

    /**
     * Deprecated use {@link PromiseCombiner#PromiseCombiner(EventExecutor)}.
     */
    @Deprecated
    public PromiseCombiner() {
        this(ImmediateEventExecutor.INSTANCE);
    }

    /**
     * The {@link EventExecutor} to use for notifications. You must call {@link #add(Future)}, {@link #addAll(Future[])}
     * and {@link #finish(Promise)} from within the {@link EventExecutor} thread.
     *
     * @param executor the {@link EventExecutor} to use for notifications.
     */
    public PromiseCombiner(EventExecutor c) {
        this.executor = ObjectUtil.checkNotNull(c, "executor");
    }

    /**
     * Adds a new promise to be combined. New promises may be added until an aggregate promise is added via the
     * {@link PromiseCombiner#finish(Promise)} method.
     *
     * @param promise the promise to add to this promise combiner
     *
     * @deprecated Replaced by {@link PromiseCombiner#add(Future)}.
     */
    @Deprecated
    public void d(Promise d) {
        d((Future) d);
    }

    /**
     * Adds a new future to be combined. New futures may be added until an aggregate promise is added via the
     * {@link PromiseCombiner#finish(Promise)} method.
     *
     * @param future the future to add to this promise combiner
     */
    @SuppressWarnings({ "unchecked", "rawtypes" })
    public void d(Future e) {
        i();
        g();
        ++expectedCount;
        e.addListener(listener);
    }

    /**
     * Adds new promises to be combined. New promises may be added until an aggregate promise is added via the
     * {@link PromiseCombiner#finish(Promise)} method.
     *
     * @param promises the promises to add to this promise combiner
     *
     * @deprecated Replaced by {@link PromiseCombiner#addAll(Future[])}
     */
    @Deprecated
    public void e(Promise... f) {
        e((Future[]) f);
    }

    /**
     * Adds new futures to be combined. New futures may be added until an aggregate promise is added via the
     * {@link PromiseCombiner#finish(Promise)} method.
     *
     * @param futures the futures to add to this promise combiner
     */
    @SuppressWarnings({ "unchecked", "rawtypes" })
    public void e(Future... g) {
        for (Future h : g) {
            this.d(h);
        }
    }

    /**
     * <p>Sets the promise to be notified when all combined futures have finished. If all combined futures succeed,
     * then the aggregate promise will succeed. If one or more combined futures fails, then the aggregate promise will
     * fail with the cause of one of the failed futures. If more than one combined future fails, then exactly which
     * failure will be assigned to the aggregate promise is undefined.</p>
     *
     * <p>After this method is called, no more futures may be added via the {@link PromiseCombiner#add(Future)} or
     * {@link PromiseCombiner#addAll(Future[])} methods.</p>
     *
     * @param aggregatePromise the promise to notify when all combined futures have finished
     */
    public void f(Promise<Void> i) {
        ObjectUtil.checkNotNull(i, "aggregatePromise");
        g();
        if (this.aggregatePromise != null) {
            throw new IllegalStateException("Already finished");
        }
        this.aggregatePromise = i;
        if (doneCount == expectedCount) {
            h();
        }
    }

    private void g() {
        if (!executor.inEventLoop()) {
            throw new IllegalStateException("Must be called from EventExecutor thread");
        }
    }

    private boolean h() {
        return (cause == null) ? aggregatePromise.trySuccess(null) : aggregatePromise.tryFailure(cause);
    }

    private void i() {
        if (aggregatePromise != null) {
            throw new IllegalStateException("Adding promises is not allowed after finished adding");
        }
    }
}
