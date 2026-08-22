package org.apache.commons.imaging.formats.png.chunks;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import org.apache.commons.imaging.ImageReadException;
import org.apache.commons.imaging.common.BinaryFunctions;
import org.apache.commons.imaging.formats.png.GammaCorrection;
import org.apache.commons.imaging.formats.png.chunks.PngChunk;

public class PngChunkPlte
extends PngChunk {
    private final int[] rgb;

    public PngChunkPlte(int length, int chunkType, int crc, byte[] bytes) throws ImageReadException, IOException {
        super(length, chunkType, crc, bytes);
        ByteArrayInputStream is = new ByteArrayInputStream(bytes);
        if (length % 3 != 0) {
            throw new ImageReadException("PLTE: wrong length: " + length);
        }
        int count = length / 3;
        this.rgb = new int[count];
        for (int i = 0; i < count; ++i) {
            byte red = BinaryFunctions.readByte("red[" + i + "]", is, "Not a Valid Png File: PLTE Corrupt");
            byte green = BinaryFunctions.readByte("green[" + i + "]", is, "Not a Valid Png File: PLTE Corrupt");
            byte blue = BinaryFunctions.readByte("blue[" + i + "]", is, "Not a Valid Png File: PLTE Corrupt");
            this.rgb[i] = 0xFF000000 | (0xFF & red) << 16 | (0xFF & green) << 8 | (0xFF & blue) << 0;
        }
    }

    public int[] getRgb() {
        return this.rgb;
    }

    public int getRGB(int index) throws ImageReadException {
        if (index < 0 || index >= this.rgb.length) {
            throw new ImageReadException("PNG: unknown Palette reference: " + index);
        }
        return this.rgb[index];
    }

    public void correct(GammaCorrection gammaCorrection) {
        for (int i = 0; i < this.rgb.length; ++i) {
            this.rgb[i] = gammaCorrection.correctARGB(this.rgb[i]);
        }
    }
}
