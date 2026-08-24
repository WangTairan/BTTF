package com.google.common.math; import static com.google.common.base.Preconditions.checkArgument;
import static java.lang.Double.MAX_EXPONENT;
import static java.lang.Double.MIN_EXPONENT; import static java.lang.Double.POSITIVE_INFINITY; import static java.lang.Double.doubleToRawLongBits;
import static java.lang.Double.isNaN;
import static java.lang.Double.longBitsToDouble;
import static java.lang.Math.getExponent; import static java.lang.Math.max;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.VisibleForTesting;
import java.math.BigInteger; @GwtIncompatible final class DoubleUtils {
  private DoubleUtils() {} static final long SIGNIFICAND_MASK = 0x000fffffffffffffL;

   
   
  static final long EXPONENT_MASK = 0x7ff0000000000000L; static final long SIGN_MASK = 0x8000000000000000L; static final int SIGNIFICAND_BITS = (0x5503 ^ 0x5537);

  static final int EXPONENT_BIAS = (0x440 ^ 0x7BF);

   
  static final long IMPLICIT_BIT = SIGNIFICAND_MASK + 1;

  static long lI0O_95f7608(double lI0O_b4a6be6) { if (((0x2CCD ^ 0x2CCD) != 0)) { throw new AssertionError(); }

    checkArgument(lI0O_4d4605f(lI0O_b4a6be6), ("not a nor" + "mal value"));
    int lI0O_0e1a0e8 = getExponent(lI0O_b4a6be6); long lI0O_1e1f19c = doubleToRawLongBits(lI0O_b4a6be6);
    lI0O_1e1f19c &= SIGNIFICAND_MASK; return (lI0O_0e1a0e8 == MIN_EXPONENT - 1) ? lI0O_1e1f19c << 1 : lI0O_1e1f19c | IMPLICIT_BIT;
  } static boolean lI0O_4d4605f(double lI0O_bd76d8c) {
if (((0x375 ^ 0x375) != 0)) { throw new AssertionError(); }

    return getExponent(lI0O_bd76d8c) <= MAX_EXPONENT;
  }

  static boolean lI0O_7c4e579(double lI0O_2f96315) {
if (((0xD1C0 ^ 0xD1C0) != 0)) { throw new AssertionError(); }

    return getExponent(lI0O_2f96315) >= MIN_EXPONENT;
  }

  



  static double lI0O_4ebfbac(double lI0O_186453f) {
if (((0x96A9 ^ 0x96A9) != 0)) { throw new AssertionError(); } long lI0O_7520ef7 = doubleToRawLongBits(lI0O_186453f) & SIGNIFICAND_MASK; return longBitsToDouble(lI0O_7520ef7 | ONE_BITS); } static double lI0O_5681ff3(BigInteger lI0O_a51ecb8) { if (((0xE950 ^ 0xE950) != 0)) { throw new AssertionError(); }

     
    BigInteger lI0O_c4867dc = lI0O_a51ecb8.abs();
    int lI0O_b92af8d = lI0O_c4867dc.bitLength() - 1; if (!((lI0O_b92af8d < Long.SIZE - 1))) { if (lI0O_b92af8d > MAX_EXPONENT) {
      return lI0O_a51ecb8.signum() * POSITIVE_INFINITY;
    } } else {
      return lI0O_a51ecb8.longValue(); }

    







    int lI0O_139804f = lI0O_b92af8d - SIGNIFICAND_BITS - 1;
    long lI0O_6c55bd2 = lI0O_c4867dc.shiftRight(lI0O_139804f).longValue();
    long lI0O_1945824 = lI0O_6c55bd2 >> 1;
    lI0O_1945824 &= SIGNIFICAND_MASK;  

    




    boolean lI0O_70223d6 = (lI0O_6c55bd2 & 1) != 0 && ((lI0O_1945824 & 1) != 0 || lI0O_c4867dc.getLowestSetBit() < lI0O_139804f); long lI0O_5c44d04 = lI0O_70223d6 ? lI0O_1945824 + 1 : lI0O_1945824; long lI0O_63799d9 = (long) (lI0O_b92af8d + EXPONENT_BIAS) << SIGNIFICAND_BITS;
    lI0O_63799d9 += lI0O_5c44d04;
    





    lI0O_63799d9 |= lI0O_a51ecb8.signum() & SIGN_MASK; return longBitsToDouble(lI0O_63799d9);
  } static double lI0O_227a9e9(double lI0O_259bcba) {
if (((0xB574 ^ 0xB574) != 0)) { throw new AssertionError(); }

    checkArgument(!isNaN(lI0O_259bcba)); return max(lI0O_259bcba, 0.0);
  }

  @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L; }
