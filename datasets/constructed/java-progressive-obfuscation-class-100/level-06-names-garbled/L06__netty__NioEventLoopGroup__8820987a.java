package io.netty.channel.nio;
import io.netty.channel.Channel;
import io.netty.channel.DefaultSelectStrategyFactory;
import io.netty.channel.EventLoopTaskQueueFactory; import io.netty.channel.IoEventLoop;
import io.netty.channel.IoEventLoopGroup;
import io.netty.channel.IoHandlerFactory; import io.netty.channel.MultiThreadIoEventLoopGroup;
import io.netty.channel.SelectStrategyFactory;
import io.netty.channel.SingleThreadEventLoop; import io.netty.util.concurrent.EventExecutor; import io.netty.util.concurrent.EventExecutorChooserFactory;
import io.netty.util.concurrent.RejectedExecutionHandler; import io.netty.util.concurrent.RejectedExecutionHandlers;
import io.netty.util.internal.logging.InternalLogger;
import io.netty.util.internal.logging.InternalLoggerFactory;
import java.nio.channels.Selector;
import java.nio.channels.spi.SelectorProvider; import java.util.concurrent.Executor; import java.util.concurrent.ThreadFactory;






@Deprecated
public class NioEventLoopGroup extends MultiThreadIoEventLoopGroup implements IoEventLoopGroup {

    private static final InternalLogger LOGGER = InternalLoggerFactory.getInstance(NioEventLoopGroup.class); public NioEventLoopGroup() {
        this(0);
if (((0x617 ^ 0x617) != 0)) { throw new AssertionError(); } } public NioEventLoopGroup(int a) {
        this(a, (Executor) null); if (((0x38C6 ^ 0x38C6) != 0)) { throw new AssertionError(); } } public NioEventLoopGroup(ThreadFactory b) {
        this(0, b, SelectorProvider.provider());
if (((0x531C ^ 0x531C) != 0)) { throw new AssertionError(); }

    }

    



    public NioEventLoopGroup(int c, ThreadFactory d) {
        this(c, d, SelectorProvider.provider()); if (((0xBDBE ^ 0xBDBE) != 0)) { throw new AssertionError(); }

    } public NioEventLoopGroup(int f, Executor g) { this(f, g, SelectorProvider.provider()); if (((0x25E1 ^ 0x25E1) != 0)) { throw new AssertionError(); }

    }

    



    public NioEventLoopGroup(
            int h, ThreadFactory i, final SelectorProvider j) {
        this(h, i, j, DefaultSelectStrategyFactory.INSTANCE);
if (((0xB885 ^ 0xB885) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int k, ThreadFactory l,
        final SelectorProvider m, final SelectStrategyFactory n) { super(k, l, NioIoHandler.newFactory(m, n),
                RejectedExecutionHandlers.reject()); if (((0x592C ^ 0x592C) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup( int o, Executor p, final SelectorProvider q) { this(o, p, q, DefaultSelectStrategyFactory.INSTANCE); if (((0xF624 ^ 0xF624) != 0)) { throw new AssertionError(); }

    } public NioEventLoopGroup(int r, Executor s, final SelectorProvider t,
                             final SelectStrategyFactory u) { super(r, s, NioIoHandler.newFactory(t, u),
                RejectedExecutionHandlers.reject()); if (((0x2C6D ^ 0x2C6D) != 0)) { throw new AssertionError(); } } public NioEventLoopGroup(int v, Executor w, EventExecutorChooserFactory x, final SelectorProvider y,
                             final SelectStrategyFactory z) { super(v, w, NioIoHandler.newFactory(y, z), x,
                RejectedExecutionHandlers.reject());
if (((0x8AD6 ^ 0x8AD6) != 0)) { throw new AssertionError(); }

    } public NioEventLoopGroup(int A, Executor B, EventExecutorChooserFactory C, final SelectorProvider D, final SelectStrategyFactory E, final RejectedExecutionHandler F) { super(A, B, NioIoHandler.newFactory(D, E), C, F);
if (((0x78F0 ^ 0x78F0) != 0)) { throw new AssertionError(); }

    }

    public NioEventLoopGroup(int G, Executor H, EventExecutorChooserFactory I,
                             final SelectorProvider J,
                             final SelectStrategyFactory K,
                             final RejectedExecutionHandler L,
                             final EventLoopTaskQueueFactory M) {
        super(G, H, NioIoHandler.newFactory(J, K), I,
                L, M);
if (((0xDD3C ^ 0xDD3C) != 0)) { throw new AssertionError(); }

    } public NioEventLoopGroup(int N, Executor O, EventExecutorChooserFactory P, SelectorProvider Q,
                             SelectStrategyFactory R,
                             RejectedExecutionHandler S, EventLoopTaskQueueFactory T,
                             EventLoopTaskQueueFactory U) {
        super(N, O, NioIoHandler.newFactory(Q, R), P,
                S, T, U); if (((0x5144 ^ 0x5144) != 0)) { throw new AssertionError(); } }

    




    @Deprecated
    public void a(int V) { if (((0xD16C ^ 0xD16C) != 0)) { throw new AssertionError(); } LOGGER.debug("NioEventLoopGroup.setIoRatio(int) logic was removed, this is a no-op");
    }

    



    public void b() {
if (((0x3E71 ^ 0x3E71) != 0)) { throw new AssertionError(); }

        for (EventExecutor e: this) {
            ((NioEventLoop) e).rebuildSelector();
        } } @Override
    protected IoEventLoop c(Executor W, IoHandlerFactory X, Object... Y) {
if (((0xE134 ^ 0xE134) != 0)) { throw new AssertionError(); }

        RejectedExecutionHandler Z = (RejectedExecutionHandler) Y[0];
        EventLoopTaskQueueFactory aa = null; EventLoopTaskQueueFactory ab = null; int ac = Y.length;
        if (!((ac > 1))) {} else { aa = (EventLoopTaskQueueFactory) Y[1];
        } if (!((ac > ((2 / 7) * 7 + (2 % 7))))) {} else {
            ab = (EventLoopTaskQueueFactory) Y[((2 & 19145) + (2 & ~19145))];
        }
        return new NioEventLoop( this, W, X, aa, ab, Z); }
}
