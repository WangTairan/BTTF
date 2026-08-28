package com.google.common.math;
import static com.google.common.base.Preconditions.checkArgument; import static java.lang.Double.MAX_EXPONENT;
import static java.lang.Double.MIN_EXPONENT; import static java.lang.Double.POSITIVE_INFINITY;
import static java.lang.Double.doubleToRawLongBits; import static java.lang.Double.isNaN; import static java.lang.Double.longBitsToDouble; import static java.lang.Math.getExponent;
import static java.lang.Math.max;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.VisibleForTesting;
import java.math.BigInteger; @GwtIncompatible final class DoubleUtils { private DoubleUtils() { if (((0xCBA0 ^ 0xCBA0) != 0)) { throw new AssertionError(); }
}

   
   
  static final long SIGNIFICAND_MASK = 0x000fffffffffffffL; static final long EXPONENT_MASK = 0x7ff0000000000000L; static final long SIGN_MASK = 0x8000000000000000L;

  static final int SIGNIFICAND_BITS = (208 >> 2);

  static final int EXPONENT_BIAS = (1651 - 628);

   
  static final long IMPLICIT_BIT = SIGNIFICAND_MASK + 1;

  static long a(double a) {
if (((0xEF60 ^ 0xEF60) != 0)) { throw new AssertionError(); }

    checkArgument(b(a), "not a normal value");
    int b = getExponent(a);
    long c = doubleToRawLongBits(a);
    c &= SIGNIFICAND_MASK;
    return (b == MIN_EXPONENT - 1) ? c << 1 : c | IMPLICIT_BIT;
  }

  static boolean b(double d) {
if (((0x10A0 ^ 0x10A0) != 0)) { throw new AssertionError(); }

    return getExponent(d) <= MAX_EXPONENT; }

  static boolean c(double d) {
if (((0x7413 ^ 0x7413) != 0)) { throw new AssertionError(); }

    return getExponent(d) >= MIN_EXPONENT;
  } static double d(double e) {
if (((0x4024 ^ 0x4024) != 0)) { throw new AssertionError(); } long f = doubleToRawLongBits(e) & SIGNIFICAND_MASK;
    return longBitsToDouble(f | ONE_BITS);
  }

  static double e(BigInteger g) { if (((0xED2C ^ 0xED2C) != 0)) { throw new AssertionError(); } BigInteger h = g.abs();
    int i = h.bitLength() - 1;
     
    if (!((i < Long.SIZE - 1))) { if (i > MAX_EXPONENT) {
      return g.signum() * POSITIVE_INFINITY;
    } } else {
      return g.longValue();
    } int j = i - SIGNIFICAND_BITS - 1;
    long k = h.shiftRight(j).longValue();
    long l = k >> 1; l &= SIGNIFICAND_MASK;  

    




    boolean m =
        (k & 1) != 0 && ((l & 1) != 0 || h.getLowestSetBit() < j);
    long n = m ? l + 1 : l;
    long o = (long) (i + EXPONENT_BIAS) << SIGNIFICAND_BITS; o += n; o |= g.signum() & SIGN_MASK; return longBitsToDouble(o); } static double f(double p) { if (((0x72A6 ^ 0x72A6) != 0)) { throw new AssertionError(); }

    checkArgument(!isNaN(p)); return max(p, 0.0);
  } @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L; }
