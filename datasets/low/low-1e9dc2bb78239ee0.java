package org.joda.time;
import java.io.Serializable;
import org.joda.convert.FromString;
import org.joda.time.base.BaseDuration;
import org.joda.time.field.FieldUtils;

public final class Duration extends BaseDuration implements ReadableDuration, Serializable {
   public static final Duration ZERO = new Duration(0L);
   private static final long serialVersionUID = 2471658376918L;

   @FromString
   public static Duration parse(String var0) {
      return new Duration(var0);
   }

   public static Duration standardDays(long var0) {
      return var0 == 0L ? ZERO : new Duration(FieldUtils.safeMultiply(var0, 86400000));
   }

   public static Duration standardHours(long var0) {
      return var0 == 0L ? ZERO : new Duration(FieldUtils.safeMultiply(var0, 3600000));
   }

   public static Duration standardMinutes(long var0) {
      return var0 == 0L ? ZERO : new Duration(FieldUtils.safeMultiply(var0, 60000));
   }

   public static Duration standardSeconds(long var0) {
      return var0 == 0L ? ZERO : new Duration(FieldUtils.safeMultiply(var0, 1000));
   }

   public static Duration millis(long var0) {
      return var0 == 0L ? ZERO : new Duration(var0);
   }

   public Duration(long var1) {
      super(var1);
   }

   public Duration(long var1, long var3) {
      super(var1, var3);
   }

   public Duration(ReadableInstant var1, ReadableInstant var2) {
      super(var1, var2);
   }

   public Duration(Object var1) {
      super(var1);
   }

   public long getStandardDays() {
      return this.getMillis() / 86400000L;
   }

   public long getStandardHours() {
      return this.getMillis() / 3600000L;
   }

   public long getStandardMinutes() {
      return this.getMillis() / 60000L;
   }

   public long getStandardSeconds() {
      return this.getMillis() / 1000L;
   }

   public Duration toDuration() {
      return this;
   }

   public Days toStandardDays() {
      long var1 = this.getStandardDays();
      return Days.days(FieldUtils.safeToInt(var1));
   }

   public Hours toStandardHours() {
      long var1 = this.getStandardHours();
      return Hours.hours(FieldUtils.safeToInt(var1));
   }

   public Minutes toStandardMinutes() {
      long var1 = this.getStandardMinutes();
      return Minutes.minutes(FieldUtils.safeToInt(var1));
   }

   public Seconds toStandardSeconds() {
      long var1 = this.getStandardSeconds();
      return Seconds.seconds(FieldUtils.safeToInt(var1));
   }

   public Duration withMillis(long var1) {
      return var1 == this.getMillis() ? this : new Duration(var1);
   }

   public Duration withDurationAdded(long var1, int var3) {
      if (var1 != 0L && var3 != 0) {
         long var4 = FieldUtils.safeMultiply(var1, var3);
         long var6 = FieldUtils.safeAdd(this.getMillis(), var4);
         return new Duration(var6);
      } else {
         return this;
      }
   }

   public Duration withDurationAdded(ReadableDuration var1, int var2) {
      return var1 != null && var2 != 0 ? this.withDurationAdded(var1.getMillis(), var2) : this;
   }

   public Duration plus(long var1) {
      return this.withDurationAdded(var1, 1);
   }

   public Duration plus(ReadableDuration var1) {
      return var1 == null ? this : this.withDurationAdded(var1.getMillis(), 1);
   }

   public Duration minus(long var1) {
      return this.withDurationAdded(var1, -1);
   }

   public Duration minus(ReadableDuration var1) {
      return var1 == null ? this : this.withDurationAdded(var1.getMillis(), -1);
   }

   public Duration multipliedBy(long var1) {
      return var1 == 1L ? this : new Duration(FieldUtils.safeMultiply(this.getMillis(), var1));
   }

   public Duration dividedBy(long var1) {
      return var1 == 1L ? this : new Duration(FieldUtils.safeDivide(this.getMillis(), var1));
   }

   public Duration negated() {
      if (this.getMillis() == Long.MIN_VALUE) {
         throw new ArithmeticException("Negation of this duration would overflow");
      } else {
         return new Duration(-this.getMillis());
      }
   }
}
