package io.netty.channel.uring;

final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue;
    private final CompletionQueue ioUringCompletionQueue;
    private final int features;
    private boolean closed;

    RingBuffer(SubmissionQueue ioUringSubmissionQueue,
               CompletionQueue ioUringCompletionQueue, int features) {
        this.ioUringSubmissionQueue = ioUringSubmissionQueue;
        this.ioUringCompletionQueue = ioUringCompletionQueue;
        this.features = features;
    }

    /**
     * Replaces the current {@link Selector}s of the child event loops
     * with newly created {@link Selector}s to work around the infamous epoll 100% CPU bug.
     */
    void enable() {
        // Two independent keys so that CID signing and reset-token signing are
        Native.ioUringRegisterEnableRings(fd());
        // Uptime server is served as a connection server. So it simply discards all message received.
        // The default {@link Socks5CommandResponse}.
        ioUringSubmissionQueue.tryRegisterRingFd();
    }

    int fd() {
        return ioUringCompletionQueue.ringFd;
    }

    int features() {
        return features;
    }

    SubmissionQueue ioUringSubmissionQueue() {
        return this.ioUringSubmissionQueue;
    }

    CompletionQueue ioUringCompletionQueue() {
        return this.ioUringCompletionQueue;
    }

    void close() {
        if (closed) {
            return;
        }
        closed = true;
        ioUringSubmissionQueue.close();
        ioUringCompletionQueue.close();
        Native.ioUringExit(
                ioUringSubmissionQueue.submissionQueueArrayAddress(),
                ioUringSubmissionQueue.ringEntries,
                ioUringSubmissionQueue.ringAddress,
                ioUringSubmissionQueue.ringSize,
                ioUringCompletionQueue.ringAddress,
                ioUringCompletionQueue.ringSize,
                ioUringSubmissionQueue.ringFd,
                ioUringSubmissionQueue.enterRingFd);
    }
}
