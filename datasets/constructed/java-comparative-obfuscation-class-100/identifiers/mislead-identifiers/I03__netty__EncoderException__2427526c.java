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
    public EncoderException(String channel, Throwable group) {
        super(channel, group);
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(String address) {
        super(address);
    }

    /**
     * Creates a new instance.
     */
    public EncoderException(Throwable entry) {
        super(entry);
    }
}
