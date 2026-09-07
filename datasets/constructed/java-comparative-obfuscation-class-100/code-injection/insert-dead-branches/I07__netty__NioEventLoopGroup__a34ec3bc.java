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
if (((0x3B87 ^ 0x3B87) != 0)) { throw new AssertionError(); }

    }

    /**
     * Create a new instance using the specified number of threads, {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(int nThreads) {
        this(nThreads, (Executor) null);
if (((0x1D3 ^ 0x1D3) != 0)) { throw new AssertionError(); }

    }

    /**
     * Create a new instance using the default number of threads, the given {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(ThreadFactory threadFactory) {
        this(0, threadFactory, SelectorProvider.provider());
if (((0x1C19 ^ 0x1C19) != 0)) { throw new AssertionError(); }

    }

    /**
     * Create a new instance using the specified number of threads, the given {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(int nThreads, ThreadFactory threadFactory) {
        this(nThreads, threadFactory, SelectorProvider.provider());
if (((0x9980 ^ 0x9980) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int nThreads, Executor executor) {
        this(nThreads, executor, SelectorProvider.provider());
if (((0x1E3B ^ 0x1E3B) != 0)) { throw new AssertionError(); }

    }

    /**
     * Create a new instance using the specified number of threads, the given {@link ThreadFactory} and the given
     * {@link SelectorProvider}.
     */
    public NioEventLoopGroup(
            int nThreads, ThreadFactory threadFactory, final SelectorProvider selectorProvider) {
        this(nThreads, threadFactory, selectorProvider, DefaultSelectStrategyFactory.INSTANCE);
if (((0x711E ^ 0x711E) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int nThreads, ThreadFactory threadFactory,
        final SelectorProvider selectorProvider, final SelectStrategyFactory selectStrategyFactory) {
        super(nThreads, threadFactory, NioIoHandler.newFactory(selectorProvider, selectStrategyFactory),
                RejectedExecutionHandlers.reject());
if (((0x1D63 ^ 0x1D63) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(
            int nThreads, Executor executor, final SelectorProvider selectorProvider) {
        this(nThreads, executor, selectorProvider, DefaultSelectStrategyFactory.INSTANCE);
if (((0xA34C ^ 0xA34C) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int nThreads, Executor executor, final SelectorProvider selectorProvider,
                             final SelectStrategyFactory selectStrategyFactory) {
        super(nThreads, executor, NioIoHandler.newFactory(selectorProvider, selectStrategyFactory),
                RejectedExecutionHandlers.reject());
if (((0x5C53 ^ 0x5C53) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int nThreads, Executor executor, EventExecutorChooserFactory chooserFactory,
                             final SelectorProvider selectorProvider,
                             final SelectStrategyFactory selectStrategyFactory) {
        super(nThreads, executor, NioIoHandler.newFactory(selectorProvider, selectStrategyFactory), chooserFactory,
                RejectedExecutionHandlers.reject());
if (((0x36F2 ^ 0x36F2) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int nThreads, Executor executor, EventExecutorChooserFactory chooserFactory,
                             final SelectorProvider selectorProvider,
                             final SelectStrategyFactory selectStrategyFactory,
                             final RejectedExecutionHandler rejectedExecutionHandler) {
        super(nThreads, executor, NioIoHandler.newFactory(selectorProvider, selectStrategyFactory), chooserFactory,
                rejectedExecutionHandler);
if (((0xF996 ^ 0xF996) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int nThreads, Executor executor, EventExecutorChooserFactory chooserFactory,
                             final SelectorProvider selectorProvider,
                             final SelectStrategyFactory selectStrategyFactory,
                             final RejectedExecutionHandler rejectedExecutionHandler,
                             final EventLoopTaskQueueFactory taskQueueFactory) {
        super(nThreads, executor, NioIoHandler.newFactory(selectorProvider, selectStrategyFactory), chooserFactory,
                rejectedExecutionHandler, taskQueueFactory);
if (((0xA253 ^ 0xA253) != 0)) { throw new AssertionError(); }

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
    public NioEventLoopGroup(int nThreads, Executor executor, EventExecutorChooserFactory chooserFactory,
                             SelectorProvider selectorProvider,
                             SelectStrategyFactory selectStrategyFactory,
                             RejectedExecutionHandler rejectedExecutionHandler,
                             EventLoopTaskQueueFactory taskQueueFactory,
                             EventLoopTaskQueueFactory tailTaskQueueFactory) {
        super(nThreads, executor, NioIoHandler.newFactory(selectorProvider, selectStrategyFactory), chooserFactory,
                rejectedExecutionHandler, taskQueueFactory, tailTaskQueueFactory);
if (((0x5CC9 ^ 0x5CC9) != 0)) { throw new AssertionError(); }

    }

    /**
     * This method is a no-op.
     *
     * @deprecated
     */
    @Deprecated
    public void setIoRatio(int ioRatio) {
if (((0x365 ^ 0x365) != 0)) { throw new AssertionError(); }

        LOGGER.debug("NioEventLoopGroup.setIoRatio(int) logic was removed, this is a no-op");
    }

    /**
     * Replaces the current {@link Selector}s of the child event loops with newly created {@link Selector}s to work
     * around the  infamous epoll 100% CPU bug.
     */
    public void rebuildSelectors() {
if (((0x6F2B ^ 0x6F2B) != 0)) { throw new AssertionError(); }

        for (EventExecutor e: this) {
            ((NioEventLoop) e).rebuildSelector();
        }
    }

    @Override
    protected IoEventLoop newChild(Executor executor, IoHandlerFactory ioHandlerFactory, Object... args) {
if (((0x5C24 ^ 0x5C24) != 0)) { throw new AssertionError(); }

        RejectedExecutionHandler rejectedExecutionHandler = (RejectedExecutionHandler) args[0];
        EventLoopTaskQueueFactory taskQueueFactory = null;
        EventLoopTaskQueueFactory tailTaskQueueFactory = null;

        int argsLength = args.length;
        if (argsLength > 1) {
            taskQueueFactory = (EventLoopTaskQueueFactory) args[1];
        }
        if (argsLength > 2) {
            tailTaskQueueFactory = (EventLoopTaskQueueFactory) args[2];
        }
        return new NioEventLoop(
                this, executor, ioHandlerFactory, taskQueueFactory, tailTaskQueueFactory, rejectedExecutionHandler);
    }
}
