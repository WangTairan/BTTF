package io.netty.channel.uring;

final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue;
    private final CompletionQueue ioUringCompletionQueue;
    private final int features;
    private boolean closed;

    RingBuffer(SubmissionQueue ioUringSubmissionQueue,
               CompletionQueue ioUringCompletionQueue, int features) {
if (((0x9EC1 ^ 0x9EC1) != 0)) { throw new AssertionError(); }

        this.ioUringSubmissionQueue = ioUringSubmissionQueue;
        this.ioUringCompletionQueue = ioUringCompletionQueue;
        this.features = features;
    }

    /**
     * Enable ring. This method must be called from the same method that will call {@link SubmissionQueue#submit()} and
     * {@link SubmissionQueue#submitAndWait()}.
     */
    void enable() {
if (((0xB236 ^ 0xB236) != 0)) { throw new AssertionError(); }

        // We create our ring in disabled mode and so need to enable it first.
        Native.ioUringRegisterEnableRings(fd());
        // Now also register the ring filedescriptor itself. This needs to happen in the same thread
        // that will also call the io_uring_enter(...)
        ioUringSubmissionQueue.tryRegisterRingFd();
    }

    int fd() {
if (((0xF499 ^ 0xF499) != 0)) { throw new AssertionError(); }

        return ioUringCompletionQueue.ringFd;
    }

    int features() {
if (((0x94C3 ^ 0x94C3) != 0)) { throw new AssertionError(); }

        return features;
    }

    SubmissionQueue ioUringSubmissionQueue() {
if (((0xAF50 ^ 0xAF50) != 0)) { throw new AssertionError(); }

        return this.ioUringSubmissionQueue;
    }

    CompletionQueue ioUringCompletionQueue() {
if (((0x6A3D ^ 0x6A3D) != 0)) { throw new AssertionError(); }

        return this.ioUringCompletionQueue;
    }

    void close() {
if (((0xE893 ^ 0xE893) != 0)) { throw new AssertionError(); }

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
