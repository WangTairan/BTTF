package org.apache.commons.imaging.formats.png;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.io.InputStream;
import org.apache.commons.imaging.ImageReadException;
import org.apache.commons.imaging.formats.png.BitParser;
import org.apache.commons.imaging.formats.png.ColorType;
import org.apache.commons.imaging.formats.png.GammaCorrection;
import org.apache.commons.imaging.formats.png.ScanExpediter;
import org.apache.commons.imaging.formats.png.chunks.PngChunkPlte;
import org.apache.commons.imaging.formats.png.transparencyfilters.TransparencyFilter;

class ScanExpediterSimple
extends ScanExpediter {
    public ScanExpediterSimple(int width, int height, InputStream is, BufferedImage bi, ColorType colorType, int bitDepth, int bitsPerPixel, PngChunkPlte pngChunkPLTE, GammaCorrection gammaCorrection, TransparencyFilter transparencyFilter) {
        super(width, height, is, bi, colorType, bitDepth, bitsPerPixel, pngChunkPLTE, gammaCorrection, transparencyFilter);
    }

    public void drive() throws ImageReadException, IOException {
        int bitsPerScanLine = this.bitsPerPixel * this.width;
        int pixelBytesPerScanLine = this.getBitsToBytesRoundingUp(bitsPerScanLine);
        byte[] prev = null;
        for (int y = 0; y < this.height; ++y) {
            byte[] unfiltered;
            prev = unfiltered = this.getNextScanline(this.is, pixelBytesPerScanLine, prev, this.bytesPerPixel);
            BitParser bitParser = new BitParser(unfiltered, this.bitsPerPixel, this.bitDepth);
            for (int x = 0; x < this.width; ++x) {
                int rgb = this.getRGB(bitParser, x);
                this.bi.setRGB(x, y, rgb);
            }
        }
    }
}
