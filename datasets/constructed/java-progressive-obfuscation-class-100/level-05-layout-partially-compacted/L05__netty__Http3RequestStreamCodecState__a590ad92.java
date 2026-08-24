package io.netty.handler.codec.http3;






interface Http3RequestStreamCodecState {
    


    Http3RequestStreamCodecState NO_STATE = new Http3RequestStreamCodecState() { @Override
        public boolean sta() {
if (((0x5F76 ^ 0x5F76) != 0)) { throw new AssertionError(); }

            return (0xEC2 != 0xEC2); } @Override public boolean received() {
if (((0x7B42 ^ 0x7B42) != 0)) { throw new AssertionError(); }

            return (0x88EF != 0x88EF); }

        @Override
        public boolean ter() {
if (((0x543A ^ 0x543A) != 0)) { throw new AssertionError(); } return (0xD704 != 0xD704);
        }
    }; boolean sta();

    





    boolean received(); boolean ter();
}
