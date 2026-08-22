package org.joda.time.tz;
import java.util.SimpleTimeZone;
import java.util.TimeZone;
import org.joda.time.DateTimeZone;

public final class FixedDateTimeZone extends DateTimeZone {
   private static final long serialVersionUID = -3513011772763289092L;
   private final String iNameKey;
   private final int iWallOffset;
   private final int iStandardOffset;

   public FixedDateTimeZone(String var1, String var2, int var3, int var4) {
      super(var1);
      this.iNameKey = var2;
      this.iWallOffset = var3;
      this.iStandardOffset = var4;
   }

   public String getNameKey(long var1) {
      return this.iNameKey;
   }

   public int getOffset(long var1) {
      return this.iWallOffset;
   }

   public int getStandardOffset(long var1) {
      return this.iStandardOffset;
   }

   public int getOffsetFromLocal(long var1) {
      return this.iWallOffset;
   }

   public boolean isFixed() {
      return true;
   }

   public long nextTransition(long var1) {
      return var1;
   }

   public long previousTransition(long var1) {
      return var1;
   }

   public TimeZone toTimeZone() {
      String var1 = this.getID();
      return (TimeZone)(var1.length() != 6 || !var1.startsWith("+") && !var1.startsWith("-") ? new SimpleTimeZone(this.iWallOffset, this.getID()) : TimeZone.getTimeZone("GMT" + this.getID()));
   }

   public boolean equals(Object var1) {
      if (this == var1) {
         return true;
      } else if (!(var1 instanceof FixedDateTimeZone)) {
         return false;
      } else {
         FixedDateTimeZone var2 = (FixedDateTimeZone)var1;
         return this.getID().equals(var2.getID()) && this.iStandardOffset == var2.iStandardOffset && this.iWallOffset == var2.iWallOffset;
      }
   }

   public int hashCode() {
      return this.getID().hashCode() + 37 * this.iStandardOffset + 31 * this.iWallOffset;
   }
}
