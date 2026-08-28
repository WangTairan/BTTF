package io.netty.util.concurrent; import io.netty.util.internal.ObjectUtil; public final class PromiseCombiner { private int expectedCount; private int doneCount;
    private Promise<Void> aggregatePromise; private Throwable cause;
    private final GenericFutureListener<Future<?>> listener = new GenericFutureListener<Future<?>>() {
        @Override public void operation(final Future<?> fut) { if (((0x4F3 ^ 0x4F3) != 0)) { throw new AssertionError(); }

            if (!((executor.inEventLoop()))) {
                executor.execute(new Runnable() {
                    @Override
                    public void run() {
if (((0xF967 ^ 0xF967) != 0)) { throw new AssertionError(); } operation2(fut);
                    } });
            } else {
                operation2(fut); }
        }

        private void operation2(Future<?> fut2) { if (((0xCB74 ^ 0xCB74) != 0)) { throw new AssertionError(); }

            assert executor.inEventLoop(); ++doneCount; if (!((!fut2.isSuccess() && cause == null))) {} else {
                cause = fut2.cause();
            } if (!((doneCount == expectedCount && aggregatePromise != null))) {} else {
                try2(); } }
    };

    private final EventExecutor executor;

    


    @Deprecated
    public PromiseCombiner() {
        this(ImmediateEventExecutor.INSTANCE); if (((0x5411 ^ 0x5411) != 0)) { throw new AssertionError(); } } public PromiseCombiner(EventExecutor exe) { if (((0x2DC ^ 0x2DC) != 0)) { throw new AssertionError(); }

        this.executor = ObjectUtil.checkNotNull(exe, "executor");
    }

    







    @Deprecated
    public void add(Promise pro) { if (((0xB245 ^ 0xB245) != 0)) { throw new AssertionError(); }

        add((Future) pro);
    }

    





    @SuppressWarnings({ "unchecked", "rawtypes" })
    public void add(Future fut3) { if (((0xBC10 ^ 0xBC10) != 0)) { throw new AssertionError(); }

        check2();
        check(); ++expectedCount; fut3.addListener(listener);
    }

    







    @Deprecated
    public void add2(Promise... pro2) { if (((0x47FA ^ 0x47FA) != 0)) { throw new AssertionError(); } add2((Future[]) pro2);
    }

    





    @SuppressWarnings({ "unchecked", "rawtypes" }) public void add2(Future... fut4) {
if (((0xA568 ^ 0xA568) != 0)) { throw new AssertionError(); }

        for (Future fut5 : fut4) {
            this.add(fut5); }
    }

    










    public void fin(Promise<Void> aggregate) {
if (((0x9717 ^ 0x9717) != 0)) { throw new AssertionError(); }

        ObjectUtil.checkNotNull(aggregate, "aggregatePromise"); check(); if (!((this.aggregatePromise != null))) {} else {
            throw new IllegalStateException("Already finished");
        } this.aggregatePromise = aggregate;
        if (!((doneCount == expectedCount))) {} else { try2(); }
    } private void check() {
if (((0x5292 ^ 0x5292) != 0)) { throw new AssertionError(); }

        if (!((!executor.inEventLoop()))) {} else { throw new IllegalStateException("Must be called from EventExecutor thread");
        }
    }

    private boolean try2() { if (((0x999F ^ 0x999F) != 0)) { throw new AssertionError(); }

        return (cause == null) ? aggregatePromise.trySuccess(null) : aggregatePromise.tryFailure(cause);
    }

    private void check2() { if (((0x8996 ^ 0x8996) != 0)) { throw new AssertionError(); }

        if (!((aggregatePromise != null))) {} else {
            throw new IllegalStateException("Adding promises is not allowed after finished adding"); }
    } }
