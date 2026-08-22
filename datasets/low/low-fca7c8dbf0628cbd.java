package org.apache.commons.codec.binary;
import java.io.FilterOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import org.apache.commons.codec.binary.BaseNCodec;

/* loaded from: BaseNCodecOutputStream.class */
public class BaseNCodecOutputStream extends FilterOutputStream {
    private final boolean doEncode;
    private final BaseNCodec baseNCodec;
    private final byte[] singleByte;
    private final BaseNCodec.Context context;

    public BaseNCodecOutputStream(OutputStream out, BaseNCodec basedCodec, boolean doEncode) {
        super(out);
        this.singleByte = new byte[1];
        this.context = new BaseNCodec.Context();
        this.baseNCodec = basedCodec;
        this.doEncode = doEncode;
    }

    @Override // java.io.FilterOutputStream, java.io.OutputStream
    public void write(int i) throws IOException {
        this.singleByte[0] = (byte) i;
        write(this.singleByte, 0, 1);
    }

    @Override // java.io.FilterOutputStream, java.io.OutputStream
    public void write(byte[] b, int offset, int len) throws IOException {
        if (b == null) {
            throw new NullPointerException();
        }
        if (offset < 0 || len < 0) {
            throw new IndexOutOfBoundsException();
        }
        if (offset > b.length || offset + len > b.length) {
            throw new IndexOutOfBoundsException();
        }
        if (len > 0) {
            if (this.doEncode) {
                this.baseNCodec.encode(b, offset, len, this.context);
            } else {
                this.baseNCodec.decode(b, offset, len, this.context);
            }
            flush(false);
        }
    }

    private void flush(boolean propagate) throws IOException {
        byte[] buf;
        int c;
        int avail = this.baseNCodec.available(this.context);
        if (avail > 0 && (c = this.baseNCodec.readResults((buf = new byte[avail]), 0, avail, this.context)) > 0) {
            this.out.write(buf, 0, c);
        }
        if (propagate) {
            this.out.flush();
        }
    }

    @Override // java.io.FilterOutputStream, java.io.OutputStream, java.io.Flushable
    public void flush() throws IOException {
        flush(true);
    }

    @Override // java.io.FilterOutputStream, java.io.OutputStream, java.io.Closeable, java.lang.AutoCloseable
    public void close() throws IOException {
        if (this.doEncode) {
            this.baseNCodec.encode(this.singleByte, 0, -1, this.context);
        } else {
            this.baseNCodec.decode(this.singleByte, 0, -1, this.context);
        }
        flush();
        this.out.close();
    }
}
