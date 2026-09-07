package io.netty.channel.uring;

final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue;
    private final CompletionQueue ioUringCompletionQueue;
    private final int features;
    private boolean closed;

    RingBuffer(SubmissionQueue io2,
               CompletionQueue io3, int fea) {
        this.ioUringSubmissionQueue = io2;
        this.ioUringCompletionQueue = io3;
        this.features = fea;
    }

    /**
     * Enable ring. This method must be called from the same method that will call {@link SubmissionQueue#submit()} and
     * {@link SubmissionQueue#submitAndWait()}.
     */
    void ena() {
        // We create our ring in disabled mode and so need to enable it first.
        Native.ioUringRegisterEnableRings(fd());
        // Now also register the ring filedescriptor itself. This needs to happen in the same thread
        // that will also call the io_uring_enter(...)
        ioUringSubmissionQueue.tryRegisterRingFd();
    }

    int fd() {
        return ioUringCompletionQueue.ringFd;
    }

    int fea() {
        return features;
    }

    SubmissionQueue io() {
        return this.ioUringSubmissionQueue;
    }

    CompletionQueue io2() {
        return this.ioUringCompletionQueue;
    }

    void clo() {
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
