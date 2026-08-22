package org.apache.commons.imaging.formats.tiff.datareaders;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteOrder;

class BitInputStream extends InputStream {
   private final InputStream is;
   private final ByteOrder byteOrder;
   private int cache;
   private int cacheBitsRemaining;
   private long bytesRead;

   public BitInputStream(InputStream is, ByteOrder byteOrder) {
      this.is = is;
      this.byteOrder = byteOrder;
   }

   public int read() throws IOException {
      if (this.cacheBitsRemaining > 0) {
         throw new IOException("BitInputStream: incomplete bit read");
      } else {
         return this.is.read();
      }
   }

   public final int readBits(int count) throws IOException {
      if (count < 8) {
         if (this.cacheBitsRemaining == 0) {
            this.cache = this.is.read();
            this.cacheBitsRemaining = 8;
            ++this.bytesRead;
         }

         if (count > this.cacheBitsRemaining) {
            throw new IOException("BitInputStream: can't read bit fields across bytes");
         }

         this.cacheBitsRemaining -= count;
         int bits = this.cache >> this.cacheBitsRemaining;
         switch (count) {
            case 1:
               return bits & 1;
            case 2:
               return bits & 3;
            case 3:
               return bits & 7;
            case 4:
               return bits & 15;
            case 5:
               return bits & 31;
            case 6:
               return bits & 63;
            case 7:
               return bits & 127;
         }
      }

      if (this.cacheBitsRemaining > 0) {
         throw new IOException("BitInputStream: incomplete bit read");
      } else if (count == 8) {
         ++this.bytesRead;
         return this.is.read();
      } else {
         if (this.byteOrder == ByteOrder.BIG_ENDIAN) {
            if (count == 16) {
               this.bytesRead += 2L;
               return this.is.read() << 8 | this.is.read() << 0;
            }

            if (count == 24) {
               this.bytesRead += 3L;
               return this.is.read() << 16 | this.is.read() << 8 | this.is.read() << 0;
            }

            if (count == 32) {
               this.bytesRead += 4L;
               return this.is.read() << 24 | this.is.read() << 16 | this.is.read() << 8 | this.is.read() << 0;
            }
         } else {
            if (count == 16) {
               this.bytesRead += 2L;
               return this.is.read() << 0 | this.is.read() << 8;
            }

            if (count == 24) {
               this.bytesRead += 3L;
               return this.is.read() << 0 | this.is.read() << 8 | this.is.read() << 16;
            }

            if (count == 32) {
               this.bytesRead += 4L;
               return this.is.read() << 0 | this.is.read() << 8 | this.is.read() << 16 | this.is.read() << 24;
            }
         }

         throw new IOException("BitInputStream: unknown error");
      }
   }

   public void flushCache() {
      this.cacheBitsRemaining = 0;
   }

   public long getBytesRead() {
      return this.bytesRead;
   }
}
