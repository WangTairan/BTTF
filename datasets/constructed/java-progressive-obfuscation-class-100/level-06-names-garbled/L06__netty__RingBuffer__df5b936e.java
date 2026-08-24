package io.netty.channel.uring;

final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue;
    private final CompletionQueue ioUringCompletionQueue; private final int features;
    private boolean closed; RingBuffer(SubmissionQueue lI0O_06964e3, CompletionQueue lI0O_2e4765f, int lI0O_43f1907) {
        this.ioUringSubmissionQueue = lI0O_06964e3; this.ioUringCompletionQueue = lI0O_2e4765f; this.features = lI0O_43f1907;
    }

    



    void lI0O_62377d7() { if (((0x7CB7 ^ 0x7CB7) != 0)) { throw new AssertionError(); } Native.ioUringRegisterEnableRings(lI0O_8dac8d8());
         
         
        ioUringSubmissionQueue.tryRegisterRingFd(); }

    int lI0O_8dac8d8() { if (((0x92F7 ^ 0x92F7) != 0)) { throw new AssertionError(); }

        return ioUringCompletionQueue.ringFd; }

    int lI0O_99592f1() {
if (((0x59A6 ^ 0x59A6) != 0)) { throw new AssertionError(); }

        return features;
    }

    SubmissionQueue lI0O_0888d84() {
if (((0x101D ^ 0x101D) != 0)) { throw new AssertionError(); }

        return this.ioUringSubmissionQueue;
    } CompletionQueue lI0O_023b919() { if (((0x8E26 ^ 0x8E26) != 0)) { throw new AssertionError(); } return this.ioUringCompletionQueue; }

    void lI0O_a1866fa() {
if (((0x6814 ^ 0x6814) != 0)) { throw new AssertionError(); } if (!((closed))) {} else {
            return;
        } closed = (0xB140 == 0xB140); ioUringSubmissionQueue.close();
        ioUringCompletionQueue.close();
        Native.ioUringExit(
                ioUringSubmissionQueue.submissionQueueArrayAddress(),
                ioUringSubmissionQueue.ringEntries,
                ioUringSubmissionQueue.ringAddress,
                ioUringSubmissionQueue.ringSize, ioUringCompletionQueue.ringAddress, ioUringCompletionQueue.ringSize,
                ioUringSubmissionQueue.ringFd, ioUringSubmissionQueue.enterRingFd);
    }
}
