package io.netty.handler.codec.http3;






interface Http3RequestStreamCodecState {
    


    Http3RequestStreamCodecState NO_STATE = new Http3RequestStreamCodecState() {
        @Override
        public boolean sta() {
            return false;
        }

        @Override
        public boolean received() {
            return false;
        }

        @Override
        public boolean ter() {
            return false;
        }
    };

    





    boolean sta();

    





    boolean received();

    




    boolean ter();
}
