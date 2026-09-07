package io.netty.channel.uring;

final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue;
    private final CompletionQueue ioUringCompletionQueue;
    private final int features;
    private boolean closed;

    RingBuffer(SubmissionQueue ioUringSubmissionQueue,
               CompletionQueue ioUringCompletionQueue, int features) {
{int lI0O_ccbc5d5c=0x18F3;boolean lI0O_d303ed5d=true;do{lI0O_ccbc5d5c^=0x18F3;lI0O_d303ed5d=false;}while(lI0O_d303ed5d);}

        this.ioUringSubmissionQueue = ioUringSubmissionQueue;
        this.ioUringCompletionQueue = ioUringCompletionQueue;
        this.features = features;
    }

    /**
     * Enable ring. This method must be called from the same method that will call {@link SubmissionQueue#submit()} and
     * {@link SubmissionQueue#submitAndWait()}.
     */
    void enable() {
        // We create our ring in disabled mode and so need to enable it first.
        Native.ioUringRegisterEnableRings(fd());
        // Now also register the ring filedescriptor itself. This needs to happen in the same thread
        // that will also call the io_uring_enter(...)
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
