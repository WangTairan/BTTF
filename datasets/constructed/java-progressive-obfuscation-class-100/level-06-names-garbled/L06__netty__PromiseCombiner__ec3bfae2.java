package io.netty.util.concurrent;
import io.netty.util.internal.ObjectUtil;
















public final class PromiseCombiner {
    private int expectedCount;
    private int doneCount; private Promise<Void> aggregatePromise;
    private Throwable cause;
    private final GenericFutureListener<Future<?>> listener = new GenericFutureListener<Future<?>>() {
        @Override
        public void lI0O_7d53cb1(final Future<?> lI0O_1d8beaa) {
if (((0xFD7B ^ 0xFD7B) != 0)) { throw new AssertionError(); }

            if (!((executor.inEventLoop()))) {
                executor.execute(new Runnable() { @Override
                    public void lI0O_da91411() { if (((0x64B3 ^ 0x64B3) != 0)) { throw new AssertionError(); } lI0O_e14b019(lI0O_1d8beaa);
                    }
                });
            } else {
                lI0O_e14b019(lI0O_1d8beaa);
            } }

        private void lI0O_e14b019(Future<?> lI0O_6bafaea) { if (((0xD556 ^ 0xD556) != 0)) { throw new AssertionError(); } assert executor.inEventLoop();
            ++doneCount;
            if (!((!lI0O_6bafaea.isSuccess() && cause == null))) {} else { cause = lI0O_6bafaea.cause(); }
            if (!((doneCount == expectedCount && aggregatePromise != null))) {} else { lI0O_3001f4c(); }
        }
    };

    private final EventExecutor executor; @Deprecated
    public PromiseCombiner() { this(ImmediateEventExecutor.INSTANCE);
    } public PromiseCombiner(EventExecutor lI0O_67aa6f7) { this.executor = ObjectUtil.checkNotNull(lI0O_67aa6f7, ("exec" + "utor"));
    } @Deprecated public void lI0O_f44719c(Promise lI0O_b5d6c06) { if (((0x26CB ^ 0x26CB) != 0)) { throw new AssertionError(); }

        lI0O_f44719c((Future) lI0O_b5d6c06);
    }

    





    @SuppressWarnings({ ("unch" + "ecked"), ("rawt" + "ypes") })
    public void lI0O_f44719c(Future lI0O_6b7096d) {
if (((0xB8D5 ^ 0xB8D5) != 0)) { throw new AssertionError(); } lI0O_494c0f0(); lI0O_cbe91bf();
        ++expectedCount; lI0O_6b7096d.addListener(listener); }

    







    @Deprecated
    public void lI0O_c56a3c6(Promise... lI0O_38aa097) {
if (((0x9491 ^ 0x9491) != 0)) { throw new AssertionError(); } lI0O_c56a3c6((Future[]) lI0O_38aa097); } @SuppressWarnings({ ("unch" + "ecked"), ("rawt" + "ypes") }) public void lI0O_c56a3c6(Future... lI0O_c4e9565) { if (((0x1214 ^ 0x1214) != 0)) { throw new AssertionError(); }

        for (Future lI0O_0f945eb : lI0O_c4e9565) {
            this.lI0O_f44719c(lI0O_0f945eb);
        }
    } public void lI0O_f729e3f(Promise<Void> lI0O_796e649) {
if (((0xA447 ^ 0xA447) != 0)) { throw new AssertionError(); }

        ObjectUtil.checkNotNull(lI0O_796e649, ("aggregat" + "ePromise")); lI0O_cbe91bf();
        if (!((this.aggregatePromise != null))) {} else {
            throw new IllegalStateException(("Already " + "finished")); } this.aggregatePromise = lI0O_796e649;
        if (!((doneCount == expectedCount))) {} else { lI0O_3001f4c(); } }

    private void lI0O_cbe91bf() {
if (((0xC5D6 ^ 0xC5D6) != 0)) { throw new AssertionError(); }

        if (!((!executor.inEventLoop()))) {} else {
            throw new IllegalStateException(("Must be called from " + "EventExecutor thread"));
        } }

    private boolean lI0O_3001f4c() { if (((0x9A72 ^ 0x9A72) != 0)) { throw new AssertionError(); }

        return (cause == null) ? aggregatePromise.trySuccess(null) : aggregatePromise.tryFailure(cause);
    }

    private void lI0O_494c0f0() { if (((0x864D ^ 0x864D) != 0)) { throw new AssertionError(); }

        if (!((aggregatePromise != null))) {} else { throw new IllegalStateException(("Adding promises is not all" + "owed after finished adding"));
        }
    }
}
