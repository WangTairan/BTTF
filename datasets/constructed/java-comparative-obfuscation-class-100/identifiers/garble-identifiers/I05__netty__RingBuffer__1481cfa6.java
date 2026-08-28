package io.netty.channel.uring;

final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue;
    private final CompletionQueue ioUringCompletionQueue;
    private final int features;
    private boolean closed;

    RingBuffer(SubmissionQueue a,
               CompletionQueue b, int c) {
        this.ioUringSubmissionQueue = a;
        this.ioUringCompletionQueue = b;
        this.features = c;
    }

    /**
     * Enable ring. This method must be called from the same method that will call {@link SubmissionQueue#submit()} and
     * {@link SubmissionQueue#submitAndWait()}.
     */
    void a() {
        // We create our ring in disabled mode and so need to enable it first.
        Native.ioUringRegisterEnableRings(b());
        // Now also register the ring filedescriptor itself. This needs to happen in the same thread
        // that will also call the io_uring_enter(...)
        ioUringSubmissionQueue.tryRegisterRingFd();
    }

    int b() {
        return ioUringCompletionQueue.ringFd;
    }

    int c() {
        return features;
    }

    SubmissionQueue d() {
        return this.ioUringSubmissionQueue;
    }

    CompletionQueue e() {
        return this.ioUringCompletionQueue;
    }

    void f() {
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
