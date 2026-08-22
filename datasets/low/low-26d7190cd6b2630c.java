package org.apache.commons.imaging.formats.icns;

final class Rle24Compression {
   private Rle24Compression() {
   }

   public static byte[] decompress(int width, int height, byte[] data) {
      int pixelCount = width * height;
      byte[] result = new byte[4 * pixelCount];
      int dataPos = 0;
      if (width >= 128 && height >= 128) {
         dataPos = 4;
      }

      label50:
      for(int band = 1; band <= 3; ++band) {
         int remaining = pixelCount;
         int resultPos = 0;

         while(true) {
            while(true) {
               if (remaining <= 0) {
                  continue label50;
               }

               int count;
               int i;
               if ((data[dataPos] & 128) != 0) {
                  count = (255 & data[dataPos]) - 125;

                  for(i = 0; i < count; ++i) {
                     result[band + 4 * resultPos++] = data[dataPos + 1];
                  }

                  dataPos += 2;
                  remaining -= count;
               } else {
                  count = (255 & data[dataPos]) + 1;
                  ++dataPos;

                  for(i = 0; i < count; ++i) {
                     result[band + 4 * resultPos++] = data[dataPos++];
                  }

                  remaining -= count;
               }
            }
         }
      }

      return result;
   }
}
