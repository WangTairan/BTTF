package io.netty.channel.nio;
import io.netty.channel.Channel;
import io.netty.channel.DefaultSelectStrategyFactory;
import io.netty.channel.EventLoopTaskQueueFactory;
import io.netty.channel.IoEventLoop;
import io.netty.channel.IoEventLoopGroup;
import io.netty.channel.IoHandlerFactory;
import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.SelectStrategyFactory;
import io.netty.channel.SingleThreadEventLoop;
import io.netty.util.concurrent.EventExecutor;
import io.netty.util.concurrent.EventExecutorChooserFactory;
import io.netty.util.concurrent.RejectedExecutionHandler;
import io.netty.util.concurrent.RejectedExecutionHandlers;
import io.netty.util.internal.logging.InternalLogger;
import io.netty.util.internal.logging.InternalLoggerFactory;
import java.nio.channels.Selector;
import java.nio.channels.spi.SelectorProvider;
import java.util.concurrent.Executor;
import java.util.concurrent.ThreadFactory;

/**
 * {@link MultiThreadIoEventLoopGroup} implementation which is used for NIO {@link Selector} based {@link Channel}s.
 *
 * @deprecated Use {@link MultiThreadIoEventLoopGroup} with {@link NioIoHandler#newFactory()}.
 */
@Deprecated
public class NioEventLoopGroup extends MultiThreadIoEventLoopGroup implements IoEventLoopGroup {

    private static final InternalLogger LOGGER = InternalLoggerFactory.getInstance(NioEventLoopGroup.class);

    /**
     * Create a new instance using the default number of threads, the default {@link ThreadFactory} and
     * the {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup() {
        this(0);
    }

    /**
     * Create a new instance using the specified number of threads, {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(int a) {
        this(a, (Executor) null);
    }

    /**
     * Create a new instance using the default number of threads, the given {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(ThreadFactory b) {
        this(0, b, SelectorProvider.provider());
    }

    /**
     * Create a new instance using the specified number of threads, the given {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(int c, ThreadFactory d) {
        this(c, d, SelectorProvider.provider());
    }

    public NioEventLoopGroup(int f, Executor g) {
        this(f, g, SelectorProvider.provider());
    }

    /**
     * Create a new instance using the specified number of threads, the given {@link ThreadFactory} and the given
     * {@link SelectorProvider}.
     */
    public NioEventLoopGroup(
            int h, ThreadFactory i, final SelectorProvider j) {
        this(h, i, j, DefaultSelectStrategyFactory.INSTANCE);
    }

    public NioEventLoopGroup(int k, ThreadFactory l,
        final SelectorProvider m, final SelectStrategyFactory n) {
        super(k, l, NioIoHandler.newFactory(m, n),
                RejectedExecutionHandlers.reject());
    }

    public NioEventLoopGroup(
            int o, Executor p, final SelectorProvider q) {
        this(o, p, q, DefaultSelectStrategyFactory.INSTANCE);
    }

    public NioEventLoopGroup(int r, Executor s, final SelectorProvider t,
                             final SelectStrategyFactory u) {
        super(r, s, NioIoHandler.newFactory(t, u),
                RejectedExecutionHandlers.reject());
    }

    public NioEventLoopGroup(int v, Executor w, EventExecutorChooserFactory x,
                             final SelectorProvider y,
                             final SelectStrategyFactory z) {
        super(v, w, NioIoHandler.newFactory(y, z), x,
                RejectedExecutionHandlers.reject());
    }

    public NioEventLoopGroup(int A, Executor B, EventExecutorChooserFactory C,
                             final SelectorProvider D,
                             final SelectStrategyFactory E,
                             final RejectedExecutionHandler F) {
        super(A, B, NioIoHandler.newFactory(D, E), C,
                F);
    }

    public NioEventLoopGroup(int G, Executor H, EventExecutorChooserFactory I,
                             final SelectorProvider J,
                             final SelectStrategyFactory K,
                             final RejectedExecutionHandler L,
                             final EventLoopTaskQueueFactory M) {
        super(G, H, NioIoHandler.newFactory(J, K), I,
                L, M);
    }

    /**
     * @param nThreads the number of threads that will be used by this instance.
     * @param executor the Executor to use, or {@code null} if default one should be used.
     * @param chooserFactory the {@link EventExecutorChooserFactory} to use.
     * @param selectorProvider the {@link SelectorProvider} to use.
     * @param selectStrategyFactory the {@link SelectStrategyFactory} to use.
     * @param rejectedExecutionHandler the {@link RejectedExecutionHandler} to use.
     * @param taskQueueFactory the {@link EventLoopTaskQueueFactory} to use for
     *                         {@link SingleThreadEventLoop#execute(Runnable)},
     *                         or {@code null} if default one should be used.
     * @param tailTaskQueueFactory the {@link EventLoopTaskQueueFactory} to use for
     *                             {@link SingleThreadEventLoop#executeAfterEventLoopIteration(Runnable)},
     *                             or {@code null} if default one should be used.
     */
    public NioEventLoopGroup(int N, Executor O, EventExecutorChooserFactory P,
                             SelectorProvider Q,
                             SelectStrategyFactory R,
                             RejectedExecutionHandler S,
                             EventLoopTaskQueueFactory T,
                             EventLoopTaskQueueFactory U) {
        super(N, O, NioIoHandler.newFactory(Q, R), P,
                S, T, U);
    }

    /**
     * This method is a no-op.
     *
     * @deprecated
     */
    @Deprecated
    public void a(int V) {
        LOGGER.debug("NioEventLoopGroup.setIoRatio(int) logic was removed, this is a no-op");
    }

    /**
     * Replaces the current {@link Selector}s of the child event loops with newly created {@link Selector}s to work
     * around the  infamous epoll 100% CPU bug.
     */
    public void b() {
        for (EventExecutor e: this) {
            ((NioEventLoop) e).rebuildSelector();
        }
    }

    @Override
    protected IoEventLoop c(Executor W, IoHandlerFactory X, Object... Y) {
        RejectedExecutionHandler Z = (RejectedExecutionHandler) Y[0];
        EventLoopTaskQueueFactory aa = null;
        EventLoopTaskQueueFactory ab = null;

        int ac = Y.length;
        if (ac > 1) {
            aa = (EventLoopTaskQueueFactory) Y[1];
        }
        if (ac > 2) {
            ab = (EventLoopTaskQueueFactory) Y[2];
        }
        return new NioEventLoop(
                this, W, X, aa, ab, Z);
    }
}
