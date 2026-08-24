package io.netty.handler.codec;




public class EncoderException extends CodecException {

    private static final long serialVersionUID = -5086121160476476774L; public EncoderException() { }

    


    public EncoderException(String mes, Throwable cau) {
        super(mes, cau); }

    


    public EncoderException(String mes2) {
        super(mes2);
    } public EncoderException(Throwable cau2) { super(cau2);
    }
}
