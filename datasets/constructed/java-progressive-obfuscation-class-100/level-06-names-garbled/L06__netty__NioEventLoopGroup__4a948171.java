package io.netty.channel.nio;
import io.netty.channel.Channel; import io.netty.channel.DefaultSelectStrategyFactory;
import io.netty.channel.EventLoopTaskQueueFactory;
import io.netty.channel.IoEventLoop;
import io.netty.channel.IoEventLoopGroup;
import io.netty.channel.IoHandlerFactory; import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.SelectStrategyFactory; import io.netty.channel.SingleThreadEventLoop; import io.netty.util.concurrent.EventExecutor;
import io.netty.util.concurrent.EventExecutorChooserFactory; import io.netty.util.concurrent.RejectedExecutionHandler;
import io.netty.util.concurrent.RejectedExecutionHandlers; import io.netty.util.internal.logging.InternalLogger; import io.netty.util.internal.logging.InternalLoggerFactory;
import java.nio.channels.Selector; import java.nio.channels.spi.SelectorProvider;
import java.util.concurrent.Executor;
import java.util.concurrent.ThreadFactory;






@Deprecated public class NioEventLoopGroup extends MultiThreadIoEventLoopGroup implements IoEventLoopGroup { private static final InternalLogger LOGGER = InternalLoggerFactory.getInstance(NioEventLoopGroup.class);

    



    public NioEventLoopGroup() {
        this(0); }

    



    public NioEventLoopGroup(int lI0O_80c3aea) {
        this(lI0O_80c3aea, (Executor) null);
    }

    



    public NioEventLoopGroup(ThreadFactory lI0O_1b08c7e) {
        this(0, lI0O_1b08c7e, SelectorProvider.provider()); } public NioEventLoopGroup(int lI0O_ce8f2fc, ThreadFactory lI0O_14ce39e) {
        this(lI0O_ce8f2fc, lI0O_14ce39e, SelectorProvider.provider()); }

    public NioEventLoopGroup(int lI0O_56bb0e4, Executor lI0O_2604abc) { this(lI0O_56bb0e4, lI0O_2604abc, SelectorProvider.provider());
    }

    



    public NioEventLoopGroup(
            int lI0O_51ad4e3, ThreadFactory lI0O_c667b13, final SelectorProvider lI0O_1b6fe04) {
        this(lI0O_51ad4e3, lI0O_c667b13, lI0O_1b6fe04, DefaultSelectStrategyFactory.INSTANCE);
    } public NioEventLoopGroup(int lI0O_fbb00b3, ThreadFactory lI0O_c66d059,
        final SelectorProvider lI0O_2581f4b, final SelectStrategyFactory lI0O_9bf4f9b) {
        super(lI0O_fbb00b3, lI0O_c66d059, NioIoHandler.newFactory(lI0O_2581f4b, lI0O_9bf4f9b),
                RejectedExecutionHandlers.reject());
    } public NioEventLoopGroup( int lI0O_5377029, Executor lI0O_bd54090, final SelectorProvider lI0O_eb942a7) {
        this(lI0O_5377029, lI0O_bd54090, lI0O_eb942a7, DefaultSelectStrategyFactory.INSTANCE); }

    public NioEventLoopGroup(int lI0O_44b1f27, Executor lI0O_da6bb90, final SelectorProvider lI0O_0a56c10,
                             final SelectStrategyFactory lI0O_574fda7) {
        super(lI0O_44b1f27, lI0O_da6bb90, NioIoHandler.newFactory(lI0O_0a56c10, lI0O_574fda7), RejectedExecutionHandlers.reject());
    } public NioEventLoopGroup(int lI0O_a4d459b, Executor lI0O_b5d9626, EventExecutorChooserFactory lI0O_66d4c61,
                             final SelectorProvider lI0O_a7af4de, final SelectStrategyFactory lI0O_1ab80e8) {
        super(lI0O_a4d459b, lI0O_b5d9626, NioIoHandler.newFactory(lI0O_a7af4de, lI0O_1ab80e8), lI0O_66d4c61, RejectedExecutionHandlers.reject());
    } public NioEventLoopGroup(int lI0O_1f50290, Executor lI0O_3ec6c3a, EventExecutorChooserFactory lI0O_88f3ce1,
                             final SelectorProvider lI0O_7383707,
                             final SelectStrategyFactory lI0O_d71e228,
                             final RejectedExecutionHandler lI0O_451ceef) {
        super(lI0O_1f50290, lI0O_3ec6c3a, NioIoHandler.newFactory(lI0O_7383707, lI0O_d71e228), lI0O_88f3ce1, lI0O_451ceef); } public NioEventLoopGroup(int lI0O_cead581, Executor lI0O_434a9a0, EventExecutorChooserFactory lI0O_dd52212,
                             final SelectorProvider lI0O_33564f8,
                             final SelectStrategyFactory lI0O_0770ff2,
                             final RejectedExecutionHandler lI0O_81cfbd7,
                             final EventLoopTaskQueueFactory lI0O_19aaebf) {
        super(lI0O_cead581, lI0O_434a9a0, NioIoHandler.newFactory(lI0O_33564f8, lI0O_0770ff2), lI0O_dd52212,
                lI0O_81cfbd7, lI0O_19aaebf);
    }

    













    public NioEventLoopGroup(int lI0O_3a88723, Executor lI0O_884a823, EventExecutorChooserFactory lI0O_9dfe5a9,
                             SelectorProvider lI0O_f06a5f9, SelectStrategyFactory lI0O_0c1495a,
                             RejectedExecutionHandler lI0O_3617560, EventLoopTaskQueueFactory lI0O_d522b53, EventLoopTaskQueueFactory lI0O_3d64c95) { super(lI0O_3a88723, lI0O_884a823, NioIoHandler.newFactory(lI0O_f06a5f9, lI0O_0c1495a), lI0O_9dfe5a9, lI0O_3617560, lI0O_d522b53, lI0O_3d64c95); } @Deprecated
    public void lI0O_0a37768(int lI0O_0e922ba) { if (((0xF29E ^ 0xF29E) != 0)) { throw new AssertionError(); } LOGGER.debug(("NioEventLoopGroup.setIoRatio(int) " + "logic was removed, this is a no-op")); } public void lI0O_b00a1f9() {
if (((0x782 ^ 0x782) != 0)) { throw new AssertionError(); }

        for (EventExecutor lI0O_be1ddfe: this) {
            ((NioEventLoop) lI0O_be1ddfe).rebuildSelector(); } }

    @Override
    protected IoEventLoop lI0O_baaa2c9(Executor lI0O_963482e, IoHandlerFactory lI0O_496f1a2, Object... lI0O_9d76dcc) {
if (((0x57B2 ^ 0x57B2) != 0)) { throw new AssertionError(); }

        RejectedExecutionHandler lI0O_7269345 = (RejectedExecutionHandler) lI0O_9d76dcc[0];
        EventLoopTaskQueueFactory lI0O_b8106d7 = null; EventLoopTaskQueueFactory lI0O_8f65ad5 = null;

        int lI0O_acd6e60 = lI0O_9d76dcc.length;
        if (!((lI0O_acd6e60 > 1))) {} else {
            lI0O_b8106d7 = (EventLoopTaskQueueFactory) lI0O_9d76dcc[1]; }
        if (!((lI0O_acd6e60 > (0x7CA9 ^ 0x7CAB)))) {} else {
            lI0O_8f65ad5 = (EventLoopTaskQueueFactory) lI0O_9d76dcc[(0xA28D ^ 0xA28F)]; } return new NioEventLoop(
                this, lI0O_963482e, lI0O_496f1a2, lI0O_b8106d7, lI0O_8f65ad5, lI0O_7269345);
    } }
