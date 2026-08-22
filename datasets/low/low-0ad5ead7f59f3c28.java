package org.apache.commons.imaging.formats.png;
import org.apache.commons.imaging.ImageReadException;

class BitParser {
   private final byte[] bytes;
   private final int bitsPerPixel;
   private final int bitDepth;

   public BitParser(byte[] bytes, int bitsPerPixel, int bitDepth) {
      this.bytes = bytes;
      this.bitsPerPixel = bitsPerPixel;
      this.bitDepth = bitDepth;
   }

   public int getSample(int pixelIndexInScanline, int sampleIndex) throws ImageReadException {
      int pixelIndexBits = this.bitsPerPixel * pixelIndexInScanline;
      int sampleIndexBits = pixelIndexBits + sampleIndex * this.bitDepth;
      int sampleIndexBytes = sampleIndexBits >> 3;
      if (this.bitDepth == 8) {
         return 255 & this.bytes[sampleIndexBytes];
      } else if (this.bitDepth < 8) {
         int b = 255 & this.bytes[sampleIndexBytes];
         int bitsToShift = 8 - ((pixelIndexBits & 7) + this.bitDepth);
         b >>= bitsToShift;
         int bitmask = (1 << this.bitDepth) - 1;
         return b & bitmask;
      } else if (this.bitDepth == 16) {
         return (255 & this.bytes[sampleIndexBytes]) << 8 | 255 & this.bytes[sampleIndexBytes + 1];
      } else {
         throw new ImageReadException("PNG: bad BitDepth: " + this.bitDepth);
      }
   }

   public int getSampleAsByte(int pixelIndexInScanline, int sampleIndex) throws ImageReadException {
      int sample = this.getSample(pixelIndexInScanline, sampleIndex);
      int rot = 8 - this.bitDepth;
      if (rot > 0) {
         sample = sample * 255 / ((1 << this.bitDepth) - 1);
      } else if (rot < 0) {
         sample >>= -rot;
      }

      return 255 & sample;
   }
}
