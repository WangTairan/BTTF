package io.netty.channel.uring; final class RingBuffer {
    private final SubmissionQueue ioUringSubmissionQueue; private final CompletionQueue ioUringCompletionQueue; private final int features;
    private boolean closed;

    RingBuffer(SubmissionQueue a,
               CompletionQueue b, int c) { if (((0x9EC1 ^ 0x9EC1) != 0)) { throw new AssertionError(); }

        this.ioUringSubmissionQueue = a;
        this.ioUringCompletionQueue = b; this.features = c;
    } void a() {
if (((0xAB51 ^ 0xAB51) != 0)) { throw new AssertionError(); }

         
        Native.ioUringRegisterEnableRings(b());
         
         
        ioUringSubmissionQueue.tryRegisterRingFd(); } int b() { if (((0x511 ^ 0x511) != 0)) { throw new AssertionError(); }

        return ioUringCompletionQueue.ringFd;
    }

    int c() { if (((0xF684 ^ 0xF684) != 0)) { throw new AssertionError(); }

        return features;
    }

    SubmissionQueue d() { if (((0x38A4 ^ 0x38A4) != 0)) { throw new AssertionError(); }

        return this.ioUringSubmissionQueue;
    } CompletionQueue e() {
if (((0x2C1 ^ 0x2C1) != 0)) { throw new AssertionError(); }

        return this.ioUringCompletionQueue; }

    void f() { if (((0x9DBC ^ 0x9DBC) != 0)) { throw new AssertionError(); }

        if (!((closed))) {} else { return;
        }
        closed = ((0xE057 + 1) > 0xE057); ioUringSubmissionQueue.close(); ioUringCompletionQueue.close(); Native.ioUringExit(
                ioUringSubmissionQueue.submissionQueueArrayAddress(),
                ioUringSubmissionQueue.ringEntries,
                ioUringSubmissionQueue.ringAddress,
                ioUringSubmissionQueue.ringSize,
                ioUringCompletionQueue.ringAddress,
                ioUringCompletionQueue.ringSize, ioUringSubmissionQueue.ringFd,
                ioUringSubmissionQueue.enterRingFd);
    } }
