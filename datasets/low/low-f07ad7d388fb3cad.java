package org.apache.commons.imaging.formats.bmp;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import org.apache.commons.imaging.common.BinaryOutputStream;
import org.apache.commons.imaging.palette.SimplePalette;

class BmpWriterPalette extends BmpWriter {
   private final SimplePalette palette;
   private final int bitsPerSample;

   public BmpWriterPalette(SimplePalette palette) {
      this.palette = palette;
      if (palette.length() <= 2) {
         this.bitsPerSample = 1;
      } else if (palette.length() <= 16) {
         this.bitsPerSample = 4;
      } else {
         this.bitsPerSample = 8;
      }

   }

   public int getPaletteSize() {
      return this.palette.length();
   }

   public int getBitsPerPixel() {
      return this.bitsPerSample;
   }

   public void writePalette(BinaryOutputStream bos) throws IOException {
      for(int i = 0; i < this.palette.length(); ++i) {
         int rgb = this.palette.getEntry(i);
         int red = 255 & rgb >> 16;
         int green = 255 & rgb >> 8;
         int blue = 255 & rgb >> 0;
         bos.write(blue);
         bos.write(green);
         bos.write(red);
         bos.write(0);
      }

   }

   public byte[] getImageData(BufferedImage src) {
      int width = src.getWidth();
      int height = src.getHeight();
      ByteArrayOutputStream baos = new ByteArrayOutputStream();
      int bitCache = 0;
      int bitsInCache = 0;
      int bytecount = 0;

      for(int y = height - 1; y >= 0; --y) {
         for(int x = 0; x < width; ++x) {
            int argb = src.getRGB(x, y);
            int rgb = 16777215 & argb;
            int index = this.palette.getPaletteIndex(rgb);
            if (this.bitsPerSample == 8) {
               baos.write(255 & index);
               ++bytecount;
            } else {
               bitCache = bitCache << this.bitsPerSample | index;
               bitsInCache += this.bitsPerSample;
               if (bitsInCache >= 8) {
                  baos.write(255 & bitCache);
                  ++bytecount;
                  bitCache = 0;
                  bitsInCache = 0;
               }
            }
         }

         if (bitsInCache > 0) {
            bitCache <<= 8 - bitsInCache;
            baos.write(255 & bitCache);
            ++bytecount;
            bitCache = 0;
            bitsInCache = 0;
         }

         while(bytecount % 4 != 0) {
            baos.write(0);
            ++bytecount;
         }
      }

      return baos.toByteArray();
   }
}
