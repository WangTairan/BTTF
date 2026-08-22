package org.apache.commons.imaging.common;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.io.RandomAccessFile;
import java.nio.ByteOrder;
import org.apache.commons.imaging.ImageReadException;
import org.apache.commons.imaging.formats.jpeg.iptc.IptcConstants;

/* loaded from: BinaryFunctions.class */
public final class BinaryFunctions {
    private BinaryFunctions() {
    }

    public static boolean startsWith(byte[] haystack, byte[] needle) {
        if (needle == null || haystack == null || needle.length > haystack.length) {
            return false;
        }
        for (int i = 0; i < needle.length; i++) {
            if (needle[i] != haystack[i]) {
                return false;
            }
        }
        return true;
    }

    public static boolean startsWith(byte[] haystack, BinaryConstant needle) {
        if (haystack == null || haystack.length < needle.size()) {
            return false;
        }
        for (int i = 0; i < needle.size(); i++) {
            if (haystack[i] != needle.get(i)) {
                return false;
            }
        }
        return true;
    }

    public static byte readByte(String name, InputStream is, String exception) throws IOException {
        int result = is.read();
        if (result < 0) {
            throw new IOException(exception);
        }
        return (byte) (255 & result);
    }

    public static byte[] readBytes(String name, InputStream is, int length) throws IOException {
        String exception = name + " could not be read.";
        return readBytes(name, is, length, exception);
    }

    public static byte[] readBytes(String name, InputStream is, int length, String exception) throws IOException {
        byte[] result = new byte[length];
        int i = 0;
        while (true) {
            int read = i;
            if (read < length) {
                int count = is.read(result, read, length - read);
                if (count < 0) {
                    throw new IOException(exception + " count: " + count + " read: " + read + " length: " + length);
                }
                i = read + count;
            } else {
                return result;
            }
        }
    }

    public static byte[] readBytes(InputStream is, int count) throws IOException {
        return readBytes("", is, count, "Unexpected EOF");
    }

    public static void readAndVerifyBytes(InputStream is, byte[] expected, String exception) throws ImageReadException, IOException {
        for (byte element : expected) {
            int data = is.read();
            byte b = (byte) (255 & data);
            if (data < 0) {
                throw new ImageReadException("Unexpected EOF.");
            }
            if (b != element) {
                throw new ImageReadException(exception);
            }
        }
    }

    public static void readAndVerifyBytes(InputStream is, BinaryConstant expected, String exception) throws ImageReadException, IOException {
        for (int i = 0; i < expected.size(); i++) {
            int data = is.read();
            byte b = (byte) (255 & data);
            if (data < 0) {
                throw new ImageReadException("Unexpected EOF.");
            }
            if (b != expected.get(i)) {
                throw new ImageReadException(exception);
            }
        }
    }

    public static void skipBytes(InputStream is, long length, String exception) throws IOException {
        long j = 0;
        while (true) {
            long total = j;
            if (length != total) {
                long skipped = is.skip(length - total);
                if (skipped < 1) {
                    throw new IOException(exception + " (" + skipped + ")");
                }
                j = total + skipped;
            } else {
                return;
            }
        }
    }

    public static byte[] remainingBytes(String name, byte[] bytes, int count) {
        return slice(bytes, count, bytes.length - count);
    }

    public static byte[] slice(byte[] bytes, int start, int count) {
        byte[] result = new byte[count];
        System.arraycopy(bytes, start, result, 0, count);
        return result;
    }

    public static byte[] head(byte[] bytes, int count) {
        if (count > bytes.length) {
            count = bytes.length;
        }
        return slice(bytes, 0, count);
    }

    public static boolean compareBytes(byte[] a, int aStart, byte[] b, int bStart, int length) {
        if (a.length < aStart + length || b.length < bStart + length) {
            return false;
        }
        for (int i = 0; i < length; i++) {
            if (a[aStart + i] != b[bStart + i]) {
                return false;
            }
        }
        return true;
    }

    public static int read4Bytes(String name, InputStream is, String exception, ByteOrder byteOrder) throws IOException {
        int result;
        int byte0 = is.read();
        int byte1 = is.read();
        int byte2 = is.read();
        int byte3 = is.read();
        if ((byte0 | byte1 | byte2 | byte3) < 0) {
            throw new IOException(exception);
        }
        if (byteOrder == ByteOrder.BIG_ENDIAN) {
            result = (byte0 << 24) | (byte1 << 16) | (byte2 << 8) | (byte3 << 0);
        } else {
            result = (byte3 << 24) | (byte2 << 16) | (byte1 << 8) | (byte0 << 0);
        }
        return result;
    }

    public static int read3Bytes(String name, InputStream is, String exception, ByteOrder byteOrder) throws IOException {
        int result;
        int byte0 = is.read();
        int byte1 = is.read();
        int byte2 = is.read();
        if ((byte0 | byte1 | byte2) < 0) {
            throw new IOException(exception);
        }
        if (byteOrder == ByteOrder.BIG_ENDIAN) {
            result = (byte0 << 16) | (byte1 << 8) | (byte2 << 0);
        } else {
            result = (byte2 << 16) | (byte1 << 8) | (byte0 << 0);
        }
        return result;
    }

    public static int read2Bytes(String name, InputStream is, String exception, ByteOrder byteOrder) throws IOException {
        int result;
        int byte0 = is.read();
        int byte1 = is.read();
        if ((byte0 | byte1) < 0) {
            throw new IOException(exception);
        }
        if (byteOrder == ByteOrder.BIG_ENDIAN) {
            result = (byte0 << 8) | byte1;
        } else {
            result = (byte1 << 8) | byte0;
        }
        return result;
    }

    public static void printCharQuad(String msg, int i) {
        System.out.println(msg + ": '" + ((char) (255 & (i >> 24))) + ((char) (255 & (i >> 16))) + ((char) (255 & (i >> 8))) + ((char) (255 & (i >> 0))) + "'");
    }

    public static void printCharQuad(PrintWriter pw, String msg, int i) {
        pw.println(msg + ": '" + ((char) (255 & (i >> 24))) + ((char) (255 & (i >> 16))) + ((char) (255 & (i >> 8))) + ((char) (255 & (i >> 0))) + "'");
    }

    public static void printByteBits(String msg, byte i) {
        System.out.println(msg + ": '" + Integer.toBinaryString(255 & i));
    }

    public static int charsToQuad(char c1, char c2, char c3, char c4) {
        return ((255 & c1) << 24) | ((255 & c2) << 16) | ((255 & c3) << 8) | ((255 & c4) << 0);
    }

    public static int findNull(byte[] src) {
        return findNull(src, 0);
    }

    public static int findNull(byte[] src, int start) {
        for (int i = start; i < src.length; i++) {
            if (src[i] == 0) {
                return i;
            }
        }
        return -1;
    }

    public static byte[] getRAFBytes(RandomAccessFile raf, long pos, int length, String exception) throws IOException {
        byte[] result = new byte[length];
        raf.seek(pos);
        int i = 0;
        while (true) {
            int read = i;
            if (read < length) {
                int count = raf.read(result, read, length - read);
                if (count < 0) {
                    throw new IOException(exception);
                }
                i = read + count;
            } else {
                return result;
            }
        }
    }

    public static void skipBytes(InputStream is, long length) throws IOException {
        skipBytes(is, length, "Couldn't skip bytes");
    }

    public static void copyStreamToStream(InputStream is, OutputStream os) throws IOException {
        byte[] buffer = new byte[IptcConstants.IMAGE_RESOURCE_BLOCK_LAYER_STATE_INFO];
        while (true) {
            int read = is.read(buffer);
            if (read > 0) {
                os.write(buffer, 0, read);
            } else {
                return;
            }
        }
    }

    public static byte[] getStreamBytes(InputStream is) throws IOException {
        ByteArrayOutputStream os = new ByteArrayOutputStream();
        copyStreamToStream(is, os);
        return os.toByteArray();
    }
}
