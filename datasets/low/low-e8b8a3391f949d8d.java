package org.apache.commons.imaging.common.mylzw;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteOrder;

public class MyBitOutputStream extends OutputStream {
   private final OutputStream os;
   private final ByteOrder byteOrder;
   private int bitsInCache;
   private int bitCache;
   private int bytesWritten;

   public MyBitOutputStream(OutputStream os, ByteOrder byteOrder) {
      this.byteOrder = byteOrder;
      this.os = os;
   }

   public void write(int value) throws IOException {
      this.writeBits(value, 8);
   }

   public void writeBits(int value, int sampleBits) throws IOException {
      int sampleMask = (1 << sampleBits) - 1;
      value &= sampleMask;
      if (this.byteOrder == ByteOrder.BIG_ENDIAN) {
         this.bitCache = this.bitCache << sampleBits | value;
      } else {
         this.bitCache |= value << this.bitsInCache;
      }

      int remainderMask;
      for(this.bitsInCache += sampleBits; this.bitsInCache >= 8; this.bitCache &= remainderMask) {
         if (this.byteOrder == ByteOrder.BIG_ENDIAN) {
            remainderMask = 255 & this.bitCache >> this.bitsInCache - 8;
            this.actualWrite(remainderMask);
            this.bitsInCache -= 8;
         } else {
            remainderMask = 255 & this.bitCache;
            this.actualWrite(remainderMask);
            this.bitCache >>= 8;
            this.bitsInCache -= 8;
         }

         remainderMask = (1 << this.bitsInCache) - 1;
      }

   }

   private void actualWrite(int value) throws IOException {
      this.os.write(value);
      ++this.bytesWritten;
   }

   public void flushCache() throws IOException {
      if (this.bitsInCache > 0) {
         int bitMask = (1 << this.bitsInCache) - 1;
         int b = bitMask & this.bitCache;
         if (this.byteOrder == ByteOrder.BIG_ENDIAN) {
            b <<= 8 - this.bitsInCache;
            this.os.write(b);
         } else {
            this.os.write(b);
         }
      }

      this.bitsInCache = 0;
      this.bitCache = 0;
   }

   public int getBytesWritten() {
      return this.bytesWritten + (this.bitsInCache > 0 ? 1 : 0);
   }
}
