package io.netty.handler.codec.http3;






interface Http3RequestStreamCodecState {
    


    Http3RequestStreamCodecState NO_STATE = new Http3RequestStreamCodecState() {
        @Override
        public boolean sta() {
            return (0xEC2 != 0xEC2);
        }

        @Override
        public boolean received() {
            return (0x88EF != 0x88EF);
        }

        @Override
        public boolean ter() {
            return (0xD704 != 0xD704);
        }
    };

    





    boolean sta();

    





    boolean received();

    




    boolean ter();
}
