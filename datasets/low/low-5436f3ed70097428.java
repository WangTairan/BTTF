package org.apache.commons.codec.binary;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import org.apache.commons.codec.binary.BaseNCodec;

/* loaded from: BaseNCodecInputStream.class */
public class BaseNCodecInputStream extends FilterInputStream {
    private final BaseNCodec baseNCodec;
    private final boolean doEncode;
    private final byte[] singleByte;
    private final BaseNCodec.Context context;

    /* JADX INFO: Access modifiers changed from: protected */
    public BaseNCodecInputStream(InputStream in, BaseNCodec baseNCodec, boolean doEncode) {
        super(in);
        this.singleByte = new byte[1];
        this.context = new BaseNCodec.Context();
        this.doEncode = doEncode;
        this.baseNCodec = baseNCodec;
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public int available() throws IOException {
        return this.context.eof ? 0 : 1;
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public synchronized void mark(int readLimit) {
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public boolean markSupported() {
        return false;
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public int read() throws IOException {
        int r;
        int read = read(this.singleByte, 0, 1);
        while (true) {
            r = read;
            if (r != 0) {
                break;
            }
            read = read(this.singleByte, 0, 1);
        }
        if (r > 0) {
            byte b = this.singleByte[0];
            return b < 0 ? 256 + b : b;
        }
        return -1;
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public int read(byte[] b, int offset, int len) throws IOException {
        if (b == null) {
            throw new NullPointerException();
        }
        if (offset < 0 || len < 0) {
            throw new IndexOutOfBoundsException();
        }
        if (offset > b.length || offset + len > b.length) {
            throw new IndexOutOfBoundsException();
        }
        if (len == 0) {
            return 0;
        }
        int i = 0;
        while (true) {
            int readLen = i;
            if (readLen == 0) {
                if (!this.baseNCodec.hasData(this.context)) {
                    byte[] buf = new byte[this.doEncode ? 4096 : 8192];
                    int c = this.in.read(buf);
                    if (this.doEncode) {
                        this.baseNCodec.encode(buf, 0, c, this.context);
                    } else {
                        this.baseNCodec.decode(buf, 0, c, this.context);
                    }
                }
                i = this.baseNCodec.readResults(b, offset, len, this.context);
            } else {
                return readLen;
            }
        }
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public synchronized void reset() throws IOException {
        throw new IOException("mark/reset not supported");
    }

    @Override // java.io.FilterInputStream, java.io.InputStream
    public long skip(long n) throws IOException {
        long todo;
        int len;
        if (n < 0) {
            throw new IllegalArgumentException("Negative skip length: " + n);
        }
        byte[] b = new byte[512];
        long j = n;
        while (true) {
            todo = j;
            if (todo <= 0 || (len = read(b, 0, (int) Math.min(b.length, todo))) == -1) {
                break;
            }
            j = todo - len;
        }
        return n - todo;
    }
}
