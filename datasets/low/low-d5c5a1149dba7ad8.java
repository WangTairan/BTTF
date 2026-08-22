package org.apache.commons.imaging.formats.bmp;
import java.io.IOException;
import java.nio.ByteOrder;
import org.apache.commons.imaging.ImageReadException;
import org.apache.commons.imaging.common.BinaryFunctions;

/* loaded from: PixelParserBitFields.class */
class PixelParserBitFields extends PixelParserSimple {
    private final int redShift;
    private final int greenShift;
    private final int blueShift;
    private final int alphaShift;
    private final int redMask;
    private final int greenMask;
    private final int blueMask;
    private final int alphaMask;
    private int bytecount;

    public PixelParserBitFields(BmpHeaderInfo bhi, byte[] colorTable, byte[] imageData) {
        super(bhi, colorTable, imageData);
        this.redMask = bhi.redMask;
        this.greenMask = bhi.greenMask;
        this.blueMask = bhi.blueMask;
        this.alphaMask = bhi.alphaMask;
        this.redShift = getMaskShift(this.redMask);
        this.greenShift = getMaskShift(this.greenMask);
        this.blueShift = getMaskShift(this.blueMask);
        this.alphaShift = this.alphaMask != 0 ? getMaskShift(this.alphaMask) : 0;
    }

    private int getMaskShift(int mask) {
        int trailingZeroes = 0;
        while ((1 & mask) == 0) {
            mask = Integer.MAX_VALUE & (mask >> 1);
            trailingZeroes++;
        }
        int maskLength = 0;
        while ((1 & mask) == 1) {
            mask = Integer.MAX_VALUE & (mask >> 1);
            maskLength++;
        }
        return trailingZeroes - (8 - maskLength);
    }

    @Override // org.apache.commons.imaging.formats.bmp.PixelParserSimple
    public int getNextRGB() throws ImageReadException, IOException {
        int data;
        if (this.bhi.bitsPerPixel == 8) {
            data = 255 & this.imageData[this.bytecount + 0];
            this.bytecount++;
        } else if (this.bhi.bitsPerPixel == 24) {
            data = BinaryFunctions.read3Bytes("Pixel", this.is, "BMP Image Data", ByteOrder.LITTLE_ENDIAN);
            this.bytecount += 3;
        } else if (this.bhi.bitsPerPixel == 32) {
            data = BinaryFunctions.read4Bytes("Pixel", this.is, "BMP Image Data", ByteOrder.LITTLE_ENDIAN);
            this.bytecount += 4;
        } else if (this.bhi.bitsPerPixel == 16) {
            data = BinaryFunctions.read2Bytes("Pixel", this.is, "BMP Image Data", ByteOrder.LITTLE_ENDIAN);
            this.bytecount += 2;
        } else {
            throw new ImageReadException("Unknown BitsPerPixel: " + this.bhi.bitsPerPixel);
        }
        int red = this.redMask & data;
        int green = this.greenMask & data;
        int blue = this.blueMask & data;
        int alpha = this.alphaMask != 0 ? this.alphaMask & data : 255;
        return ((this.alphaShift >= 0 ? alpha >> this.alphaShift : alpha << (-this.alphaShift)) << 24) | ((this.redShift >= 0 ? red >> this.redShift : red << (-this.redShift)) << 16) | ((this.greenShift >= 0 ? green >> this.greenShift : green << (-this.greenShift)) << 8) | ((this.blueShift >= 0 ? blue >> this.blueShift : blue << (-this.blueShift)) << 0);
    }

    @Override // org.apache.commons.imaging.formats.bmp.PixelParserSimple
    public void newline() throws ImageReadException, IOException {
        while (this.bytecount % 4 != 0) {
            BinaryFunctions.readByte("Pixel", this.is, "BMP Image Data");
            this.bytecount++;
        }
    }
}
