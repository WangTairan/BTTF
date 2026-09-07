package io.netty.handler.codec;

/**
 * An {@link CodecException} which is thrown by an encoder.
 */
public class EncoderException extends CodecException {

    private static final long serialVersionUID = -5086121160476476774L;

    /**
     * Creates a new instance.
     */
    public EncoderException() {
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(String a, Throwable b) {
        super(a, b);
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(String c) {
        super(c);
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(Throwable d) {
        super(d);
    }
}
