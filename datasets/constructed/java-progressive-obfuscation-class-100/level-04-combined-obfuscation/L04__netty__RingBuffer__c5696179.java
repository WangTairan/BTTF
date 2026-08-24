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
if (((0x7CB7 ^ 0x7CB7) != 0)) { throw new AssertionError(); }

         
        Native.ioUringRegisterEnableRings(fd());
         
         
        ioUringSubmissionQueue.tryRegisterRingFd();
    }

    int fd() {
if (((0x92F7 ^ 0x92F7) != 0)) { throw new AssertionError(); }

        return ioUringCompletionQueue.ringFd;
    }

    int fea() {
if (((0x59A6 ^ 0x59A6) != 0)) { throw new AssertionError(); }

        return features;
    }

    SubmissionQueue io() {
if (((0x101D ^ 0x101D) != 0)) { throw new AssertionError(); }

        return this.ioUringSubmissionQueue;
    }

    CompletionQueue io2() {
if (((0x8E26 ^ 0x8E26) != 0)) { throw new AssertionError(); }

        return this.ioUringCompletionQueue;
    }

    void clo() {
if (((0x6814 ^ 0x6814) != 0)) { throw new AssertionError(); }

        if (!((closed))) {} else {
            return;
        }
        closed = (0xB140 == 0xB140);
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
