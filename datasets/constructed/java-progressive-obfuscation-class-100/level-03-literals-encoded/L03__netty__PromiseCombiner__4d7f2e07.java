package io.netty.util.concurrent;
import io.netty.util.internal.ObjectUtil;
















public final class PromiseCombiner {
    private int expectedCount;
    private int doneCount;
    private Promise<Void> aggregatePromise;
    private Throwable cause;
    private final GenericFutureListener<Future<?>> listener = new GenericFutureListener<Future<?>>() {
        @Override
        public void operation(final Future<?> fut) {
            if (executor.inEventLoop()) {
                operation2(fut);
            } else {
                executor.execute(new Runnable() {
                    @Override
                    public void run() {
                        operation2(fut);
                    }
                });
            }
        }

        private void operation2(Future<?> fut2) {
            assert executor.inEventLoop();
            ++doneCount;
            if (!fut2.isSuccess() && cause == null) {
                cause = fut2.cause();
            }
            if (doneCount == expectedCount && aggregatePromise != null) {
                try2();
            }
        }
    };

    private final EventExecutor executor;

    


    @Deprecated
    public PromiseCombiner() {
        this(ImmediateEventExecutor.INSTANCE);
    }

    





    public PromiseCombiner(EventExecutor exe) {
        this.executor = ObjectUtil.checkNotNull(exe, "executor");
    }

    







    @Deprecated
    public void add(Promise pro) {
        add((Future) pro);
    }

    





    @SuppressWarnings({ "unchecked", "rawtypes" })
    public void add(Future fut3) {
        check2();
        check();
        ++expectedCount;
        fut3.addListener(listener);
    }

    







    @Deprecated
    public void add2(Promise... pro2) {
        add2((Future[]) pro2);
    }

    





    @SuppressWarnings({ "unchecked", "rawtypes" })
    public void add2(Future... fut4) {
        for (Future fut5 : fut4) {
            this.add(fut5);
        }
    }

    










    public void fin(Promise<Void> aggregate) {
        ObjectUtil.checkNotNull(aggregate, "aggregatePromise");
        check();
        if (this.aggregatePromise != null) {
            throw new IllegalStateException("Already finished");
        }
        this.aggregatePromise = aggregate;
        if (doneCount == expectedCount) {
            try2();
        }
    }

    private void check() {
        if (!executor.inEventLoop()) {
            throw new IllegalStateException("Must be called from EventExecutor thread");
        }
    }

    private boolean try2() {
        return (cause == null) ? aggregatePromise.trySuccess(null) : aggregatePromise.tryFailure(cause);
    }

    private void check2() {
        if (aggregatePromise != null) {
            throw new IllegalStateException("Adding promises is not allowed after finished adding");
        }
    }
}
