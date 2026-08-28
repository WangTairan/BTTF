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

    



    void ena() {
         
        Native.ioUringRegisterEnableRings(fd());
         
         
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
        closed = ((0xE057 + 1) > 0xE057);
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
