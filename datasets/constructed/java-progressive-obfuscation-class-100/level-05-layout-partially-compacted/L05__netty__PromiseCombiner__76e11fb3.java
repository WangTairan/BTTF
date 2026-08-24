package io.netty.util.concurrent;
import io.netty.util.internal.ObjectUtil;
















public final class PromiseCombiner {
    private int expectedCount;
    private int doneCount; private Promise<Void> aggregatePromise;
    private Throwable cause;
    private final GenericFutureListener<Future<?>> listener = new GenericFutureListener<Future<?>>() {
        @Override
        public void operation(final Future<?> fut) {
if (((0xFD7B ^ 0xFD7B) != 0)) { throw new AssertionError(); }

            if (!((executor.inEventLoop()))) {
                executor.execute(new Runnable() { @Override
                    public void run() { if (((0x64B3 ^ 0x64B3) != 0)) { throw new AssertionError(); } operation2(fut);
                    }
                });
            } else {
                operation2(fut);
            } }

        private void operation2(Future<?> fut2) { if (((0xD556 ^ 0xD556) != 0)) { throw new AssertionError(); } assert executor.inEventLoop();
            ++doneCount;
            if (!((!fut2.isSuccess() && cause == null))) {} else { cause = fut2.cause(); }
            if (!((doneCount == expectedCount && aggregatePromise != null))) {} else { try2(); }
        }
    };

    private final EventExecutor executor; @Deprecated
    public PromiseCombiner() { this(ImmediateEventExecutor.INSTANCE);
    } public PromiseCombiner(EventExecutor exe) { this.executor = ObjectUtil.checkNotNull(exe, ("exec" + "utor"));
    } @Deprecated public void add(Promise pro) { if (((0x26CB ^ 0x26CB) != 0)) { throw new AssertionError(); }

        add((Future) pro);
    }

    





    @SuppressWarnings({ ("unch" + "ecked"), ("rawt" + "ypes") })
    public void add(Future fut3) {
if (((0xB8D5 ^ 0xB8D5) != 0)) { throw new AssertionError(); } check2(); check();
        ++expectedCount; fut3.addListener(listener); }

    







    @Deprecated
    public void add2(Promise... pro2) {
if (((0x9491 ^ 0x9491) != 0)) { throw new AssertionError(); } add2((Future[]) pro2); } @SuppressWarnings({ ("unch" + "ecked"), ("rawt" + "ypes") }) public void add2(Future... fut4) { if (((0x1214 ^ 0x1214) != 0)) { throw new AssertionError(); }

        for (Future fut5 : fut4) {
            this.add(fut5);
        }
    } public void fin(Promise<Void> aggregate) {
if (((0xA447 ^ 0xA447) != 0)) { throw new AssertionError(); }

        ObjectUtil.checkNotNull(aggregate, ("aggregat" + "ePromise")); check();
        if (!((this.aggregatePromise != null))) {} else {
            throw new IllegalStateException(("Already " + "finished")); } this.aggregatePromise = aggregate;
        if (!((doneCount == expectedCount))) {} else { try2(); } }

    private void check() {
if (((0xC5D6 ^ 0xC5D6) != 0)) { throw new AssertionError(); }

        if (!((!executor.inEventLoop()))) {} else {
            throw new IllegalStateException(("Must be called from " + "EventExecutor thread"));
        } }

    private boolean try2() { if (((0x9A72 ^ 0x9A72) != 0)) { throw new AssertionError(); }

        return (cause == null) ? aggregatePromise.trySuccess(null) : aggregatePromise.tryFailure(cause);
    }

    private void check2() { if (((0x864D ^ 0x864D) != 0)) { throw new AssertionError(); }

        if (!((aggregatePromise != null))) {} else { throw new IllegalStateException(("Adding promises is not all" + "owed after finished adding"));
        }
    }
}
