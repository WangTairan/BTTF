package io.netty.handler.codec;

/**
 * An {@link CodecException} which is thrown by an encoder.
 */
public class EncoderException extends CodecException {

    private static final long serialVersionUID = -0x4695883f7ecc4566L;

    /**
     * Creates a new instance.
     */
    public EncoderException() {
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(String message, Throwable cause) {
        super(message, cause);
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(String message) {
        super(message);
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(Throwable cause) {
        super(cause);
    }
}
