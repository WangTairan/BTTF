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
    public NioEventLoopGroup(int n) {
        this(n, (Executor) null);
    }

    /**
     * Create a new instance using the default number of threads, the given {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(ThreadFactory thread) {
        this(0, thread, SelectorProvider.provider());
    }

    /**
     * Create a new instance using the specified number of threads, the given {@link ThreadFactory} and the
     * {@link SelectorProvider} which is returned by {@link SelectorProvider#provider()}.
     */
    public NioEventLoopGroup(int n2, ThreadFactory thread2) {
        this(n2, thread2, SelectorProvider.provider());
    }

    public NioEventLoopGroup(int n3, Executor exe) {
        this(n3, exe, SelectorProvider.provider());
    }

    /**
     * Create a new instance using the specified number of threads, the given {@link ThreadFactory} and the given
     * {@link SelectorProvider}.
     */
    public NioEventLoopGroup(
            int n4, ThreadFactory thread3, final SelectorProvider selector) {
        this(n4, thread3, selector, DefaultSelectStrategyFactory.INSTANCE);
    }

    public NioEventLoopGroup(int n5, ThreadFactory thread4,
        final SelectorProvider selector2, final SelectStrategyFactory select) {
        super(n5, thread4, NioIoHandler.newFactory(selector2, select),
                RejectedExecutionHandlers.reject());
    }

    public NioEventLoopGroup(
            int n6, Executor exe2, final SelectorProvider selector3) {
        this(n6, exe2, selector3, DefaultSelectStrategyFactory.INSTANCE);
    }

    public NioEventLoopGroup(int n7, Executor exe3, final SelectorProvider selector4,
                             final SelectStrategyFactory select2) {
        super(n7, exe3, NioIoHandler.newFactory(selector4, select2),
                RejectedExecutionHandlers.reject());
    }

    public NioEventLoopGroup(int n8, Executor exe4, EventExecutorChooserFactory chooser,
                             final SelectorProvider selector5,
                             final SelectStrategyFactory select3) {
        super(n8, exe4, NioIoHandler.newFactory(selector5, select3), chooser,
                RejectedExecutionHandlers.reject());
    }

    public NioEventLoopGroup(int n9, Executor exe5, EventExecutorChooserFactory chooser2,
                             final SelectorProvider selector6,
                             final SelectStrategyFactory select4,
                             final RejectedExecutionHandler rejected) {
        super(n9, exe5, NioIoHandler.newFactory(selector6, select4), chooser2,
                rejected);
    }

    public NioEventLoopGroup(int n10, Executor exe6, EventExecutorChooserFactory chooser3,
                             final SelectorProvider selector7,
                             final SelectStrategyFactory select5,
                             final RejectedExecutionHandler rejected2,
                             final EventLoopTaskQueueFactory task) {
        super(n10, exe6, NioIoHandler.newFactory(selector7, select5), chooser3,
                rejected2, task);
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
    public NioEventLoopGroup(int n11, Executor exe7, EventExecutorChooserFactory chooser4,
                             SelectorProvider selector8,
                             SelectStrategyFactory select6,
                             RejectedExecutionHandler rejected3,
                             EventLoopTaskQueueFactory task2,
                             EventLoopTaskQueueFactory tail) {
        super(n11, exe7, NioIoHandler.newFactory(selector8, select6), chooser4,
                rejected3, task2, tail);
    }

    /**
     * This method is a no-op.
     *
     * @deprecated
     */
    @Deprecated
    public void set(int io2) {
        LOGGER.debug("NioEventLoopGroup.setIoRatio(int) logic was removed, this is a no-op");
    }

    /**
     * Replaces the current {@link Selector}s of the child event loops with newly created {@link Selector}s to work
     * around the  infamous epoll 100% CPU bug.
     */
    public void rebuild() {
        for (EventExecutor e: this) {
            ((NioEventLoop) e).rebuildSelector();
        }
    }

    @Override
    protected IoEventLoop new2(Executor exe8, IoHandlerFactory io3, Object... arg) {
        RejectedExecutionHandler rejected4 = (RejectedExecutionHandler) arg[0];
        EventLoopTaskQueueFactory task3 = null;
        EventLoopTaskQueueFactory tail2 = null;

        int args = arg.length;
        if (args > 1) {
            task3 = (EventLoopTaskQueueFactory) arg[1];
        }
        if (args > 2) {
            tail2 = (EventLoopTaskQueueFactory) arg[2];
        }
        return new NioEventLoop(
                this, exe8, io3, task3, tail2, rejected4);
    }
}
