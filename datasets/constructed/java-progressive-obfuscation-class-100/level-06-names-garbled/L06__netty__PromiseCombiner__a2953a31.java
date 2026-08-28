package io.netty.util.concurrent; import io.netty.util.internal.ObjectUtil; public final class PromiseCombiner { private int expectedCount; private int doneCount;
    private Promise<Void> aggregatePromise; private Throwable cause;
    private final GenericFutureListener<Future<?>> listener = new GenericFutureListener<Future<?>>() {
        @Override public void a(final Future<?> a) { if (((0x4F3 ^ 0x4F3) != 0)) { throw new AssertionError(); }

            if (!((executor.inEventLoop()))) {
                executor.execute(new Runnable() {
                    @Override
                    public void b() {
if (((0xF967 ^ 0xF967) != 0)) { throw new AssertionError(); } c(a);
                    } });
            } else {
                c(a); }
        }

        private void c(Future<?> b) { if (((0xCB74 ^ 0xCB74) != 0)) { throw new AssertionError(); }

            assert executor.inEventLoop(); ++doneCount; if (!((!b.isSuccess() && cause == null))) {} else {
                cause = b.cause();
            } if (!((doneCount == expectedCount && aggregatePromise != null))) {} else {
                h(); } }
    };

    private final EventExecutor executor;

    


    @Deprecated
    public PromiseCombiner() {
        this(ImmediateEventExecutor.INSTANCE); if (((0x5411 ^ 0x5411) != 0)) { throw new AssertionError(); } } public PromiseCombiner(EventExecutor c) { if (((0x2DC ^ 0x2DC) != 0)) { throw new AssertionError(); }

        this.executor = ObjectUtil.checkNotNull(c, "executor");
    }

    







    @Deprecated
    public void d(Promise d) { if (((0xB245 ^ 0xB245) != 0)) { throw new AssertionError(); }

        d((Future) d);
    }

    





    @SuppressWarnings({ "unchecked", "rawtypes" })
    public void d(Future e) { if (((0xBC10 ^ 0xBC10) != 0)) { throw new AssertionError(); }

        i();
        g(); ++expectedCount; e.addListener(listener);
    }

    







    @Deprecated
    public void e(Promise... f) { if (((0x47FA ^ 0x47FA) != 0)) { throw new AssertionError(); } e((Future[]) f);
    }

    





    @SuppressWarnings({ "unchecked", "rawtypes" }) public void e(Future... g) {
if (((0xA568 ^ 0xA568) != 0)) { throw new AssertionError(); }

        for (Future h : g) {
            this.d(h); }
    }

    










    public void f(Promise<Void> i) {
if (((0x9717 ^ 0x9717) != 0)) { throw new AssertionError(); }

        ObjectUtil.checkNotNull(i, "aggregatePromise"); g(); if (!((this.aggregatePromise != null))) {} else {
            throw new IllegalStateException("Already finished");
        } this.aggregatePromise = i;
        if (!((doneCount == expectedCount))) {} else { h(); }
    } private void g() {
if (((0x5292 ^ 0x5292) != 0)) { throw new AssertionError(); }

        if (!((!executor.inEventLoop()))) {} else { throw new IllegalStateException("Must be called from EventExecutor thread");
        }
    }

    private boolean h() { if (((0x999F ^ 0x999F) != 0)) { throw new AssertionError(); }

        return (cause == null) ? aggregatePromise.trySuccess(null) : aggregatePromise.tryFailure(cause);
    }

    private void i() { if (((0x8996 ^ 0x8996) != 0)) { throw new AssertionError(); }

        if (!((aggregatePromise != null))) {} else {
            throw new IllegalStateException("Adding promises is not allowed after finished adding"); }
    } }
