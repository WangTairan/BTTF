package org.apache.commons.imaging.common;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Arrays;

public class BinaryConstant
implements Cloneable {
    private final byte[] value;

    public BinaryConstant(byte[] value) {
        this.value = (byte[])value.clone();
    }

    public BinaryConstant clone() throws CloneNotSupportedException {
        return (BinaryConstant)super.clone();
    }

    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }
        if (!(obj instanceof BinaryConstant)) {
            return false;
        }
        BinaryConstant other = (BinaryConstant)obj;
        return this.equals(other.value);
    }

    public boolean equals(byte[] bytes) {
        return Arrays.equals(this.value, bytes);
    }

    public boolean equals(byte[] bytes, int offset, int length) {
        if (this.value.length != length) {
            return false;
        }
        for (int i = 0; i < length; ++i) {
            if (this.value[i] == bytes[offset + i]) continue;
            return false;
        }
        return true;
    }

    public int hashCode() {
        return Arrays.hashCode(this.value);
    }

    public byte get(int i) {
        return this.value[i];
    }

    public int size() {
        return this.value.length;
    }

    public byte[] toByteArray() {
        return (byte[])this.value.clone();
    }

    public void writeTo(OutputStream os) throws IOException {
        for (byte element : this.value) {
            os.write(element);
        }
    }
}
