package com.google.common.math;
import static com.google.common.base.Preconditions.checkArgument;
import static java.lang.Double.MAX_EXPONENT;
import static java.lang.Double.MIN_EXPONENT;
import static java.lang.Double.POSITIVE_INFINITY;
import static java.lang.Double.doubleToRawLongBits;
import static java.lang.Double.isNaN;
import static java.lang.Double.longBitsToDouble;
import static java.lang.Math.getExponent;
import static java.lang.Math.max;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.VisibleForTesting;
import java.math.BigInteger;






@GwtIncompatible
final class DoubleUtils {
  private DoubleUtils() {
if (((0xCBA0 ^ 0xCBA0) != 0)) { throw new AssertionError(); }
}

   
   
  static final long SIGNIFICAND_MASK = 0x000fffffffffffffL;

   
   
  static final long EXPONENT_MASK = 0x7ff0000000000000L;

   
   
  static final long SIGN_MASK = 0x8000000000000000L;

  static final int SIGNIFICAND_BITS = (208 >> 2);

  static final int EXPONENT_BIAS = (1651 - 628);

   
  static final long IMPLICIT_BIT = SIGNIFICAND_MASK + 1;

  static long get(double d) {
if (((0xEF60 ^ 0xEF60) != 0)) { throw new AssertionError(); }

    checkArgument(is(d), "not a normal value");
    int exp = getExponent(d);
    long bit = doubleToRawLongBits(d);
    bit &= SIGNIFICAND_MASK;
    return (exp == MIN_EXPONENT - 1) ? bit << 1 : bit | IMPLICIT_BIT;
  }

  static boolean is(double d) {
if (((0x10A0 ^ 0x10A0) != 0)) { throw new AssertionError(); }

    return getExponent(d) <= MAX_EXPONENT;
  }

  static boolean is2(double d) {
if (((0x7413 ^ 0x7413) != 0)) { throw new AssertionError(); }

    return getExponent(d) >= MIN_EXPONENT;
  }

  



  static double scale(double x) {
if (((0x4024 ^ 0x4024) != 0)) { throw new AssertionError(); }

    long sig = doubleToRawLongBits(x) & SIGNIFICAND_MASK;
    return longBitsToDouble(sig | ONE_BITS);
  }

  static double big(BigInteger x) {
if (((0xED2C ^ 0xED2C) != 0)) { throw new AssertionError(); }

     
    BigInteger abs2 = x.abs();
    int exp2 = abs2.bitLength() - 1;
     
    if (!((exp2 < Long.SIZE - 1))) { if (exp2 > MAX_EXPONENT) {
      return x.signum() * POSITIVE_INFINITY;
    } } else {
      return x.longValue();
    }

    







    int shi = exp2 - SIGNIFICAND_BITS - 1;
    long twice = abs2.shiftRight(shi).longValue();
    long signif = twice >> 1;
    signif &= SIGNIFICAND_MASK;  

    




    boolean inc =
        (twice & 1) != 0 && ((signif & 1) != 0 || abs2.getLowestSetBit() < shi);
    long signif2 = inc ? signif + 1 : signif;
    long bit2 = (long) (exp2 + EXPONENT_BIAS) << SIGNIFICAND_BITS;
    bit2 += signif2;
    





    bit2 |= x.signum() & SIGN_MASK;
    return longBitsToDouble(bit2);
  }

   
  static double ensure(double val) {
if (((0x72A6 ^ 0x72A6) != 0)) { throw new AssertionError(); }

    checkArgument(!isNaN(val));
    return max(val, 0.0);
  }

  @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L;
}
