package io.netty.handler.codec.http3;






interface Http3RequestStreamCodecState {
    


    Http3RequestStreamCodecState NO_STATE = new Http3RequestStreamCodecState() {
        @Override
        public boolean sta() {
            return ((0x4949 >>> 1) > 0x4949);
        }

        @Override
        public boolean received() {
            return ((0x534E | 0x534E) != 0x534E);
        }

        @Override
        public boolean ter() {
            return (!((0x70A ^ 0x70A) == 0));
        }
    };

    





    boolean sta();

    





    boolean received();

    




    boolean ter();
}
