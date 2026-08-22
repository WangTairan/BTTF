package org.apache.commons.imaging.formats.png.chunks;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.zip.InflaterInputStream;
import org.apache.commons.imaging.ImageReadException;
import org.apache.commons.imaging.common.BinaryFunctions;
import org.apache.commons.imaging.formats.png.PngText;
import org.apache.commons.imaging.formats.png.chunks.PngTextChunk;

public class PngChunkItxt
extends PngTextChunk {
    public final String keyword;
    public final String text;
    public final String languageTag;
    public final String translatedKeyword;

    public PngChunkItxt(int length, int chunkType, int crc, byte[] bytes) throws ImageReadException, IOException {
        super(length, chunkType, crc, bytes);
        byte compressionFlag;
        int terminator = BinaryFunctions.findNull(bytes);
        if (terminator < 0) {
            throw new ImageReadException("PNG iTXt chunk keyword is not terminated.");
        }
        this.keyword = new String(bytes, 0, terminator, "ISO-8859-1");
        int index = terminator + 1;
        if ((compressionFlag = bytes[index++]) != 0 && compressionFlag != 1) {
            throw new ImageReadException("PNG iTXt chunk has invalid compression flag: " + compressionFlag);
        }
        boolean compressed = compressionFlag == 1;
        byte compressionMethod = bytes[index++];
        if (compressed && compressionMethod != 0) {
            throw new ImageReadException("PNG iTXt chunk has unexpected compression method: " + compressionMethod);
        }
        terminator = BinaryFunctions.findNull(bytes, index);
        if (terminator < 0) {
            throw new ImageReadException("PNG iTXt chunk language tag is not terminated.");
        }
        this.languageTag = new String(bytes, index, terminator - index, "ISO-8859-1");
        index = terminator + 1;
        if ((terminator = BinaryFunctions.findNull(bytes, index)) < 0) {
            throw new ImageReadException("PNG iTXt chunk translated keyword is not terminated.");
        }
        this.translatedKeyword = new String(bytes, index, terminator - index, "utf-8");
        index = terminator + 1;
        if (compressed) {
            int compressedTextLength = bytes.length - index;
            byte[] compressedText = new byte[compressedTextLength];
            System.arraycopy(bytes, index, compressedText, 0, compressedTextLength);
            this.text = new String(BinaryFunctions.getStreamBytes(new InflaterInputStream(new ByteArrayInputStream(compressedText))), "utf-8");
        } else {
            this.text = new String(bytes, index, bytes.length - index, "utf-8");
        }
    }

    public String getKeyword() {
        return this.keyword;
    }

    public String getText() {
        return this.text;
    }

    public PngText getContents() {
        return new PngText.Itxt(this.keyword, this.text, this.languageTag, this.translatedKeyword);
    }
}
