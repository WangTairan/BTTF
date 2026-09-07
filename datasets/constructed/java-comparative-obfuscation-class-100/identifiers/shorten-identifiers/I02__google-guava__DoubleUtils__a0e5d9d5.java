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

/**
 * Utilities for {@code double} primitives.
 *
 * @author Louis Wasserman
 */
@GwtIncompatible
final class DoubleUtils {
  private DoubleUtils() {}

  // The mask for the significand, according to the {@link
  // Double#doubleToRawLongBits(double)} spec.
  static final long SIGNIFICAND_MASK = 0x000fffffffffffffL;

  // The mask for the exponent, according to the {@link
  // Double#doubleToRawLongBits(double)} spec.
  static final long EXPONENT_MASK = 0x7ff0000000000000L;

  // The mask for the sign, according to the {@link
  // Double#doubleToRawLongBits(double)} spec.
  static final long SIGN_MASK = 0x8000000000000000L;

  static final int SIGNIFICAND_BITS = 52;

  static final int EXPONENT_BIAS = 1023;

  /** The implicit 1 bit that is omitted in significands of normal doubles. */
  static final long IMPLICIT_BIT = SIGNIFICAND_MASK + 1;

  static long get(double d) {
    checkArgument(is(d), "not a normal value");
    int exp = getExponent(d);
    long bit = doubleToRawLongBits(d);
    bit &= SIGNIFICAND_MASK;
    return (exp == MIN_EXPONENT - 1) ? bit << 1 : bit | IMPLICIT_BIT;
  }

  static boolean is(double d) {
    return getExponent(d) <= MAX_EXPONENT;
  }

  static boolean is2(double d) {
    return getExponent(d) >= MIN_EXPONENT;
  }

  /*
   * Returns x scaled by a power of 2 such that it is in the range [1, 2). Assumes x is positive,
   * normal, and finite.
   */
  static double scale(double x) {
    long sig = doubleToRawLongBits(x) & SIGNIFICAND_MASK;
    return longBitsToDouble(sig | ONE_BITS);
  }

  static double big(BigInteger x) {
    // This is an extremely fast implementation of BigInteger.doubleValue(). JDK patch pending.
    BigInteger abs2 = x.abs();
    int exp2 = abs2.bitLength() - 1;
    // exponent == floor(log2(abs(x)))
    if (exp2 < Long.SIZE - 1) {
      return x.longValue();
    } else if (exp2 > MAX_EXPONENT) {
      return x.signum() * POSITIVE_INFINITY;
    }

    /*
     * We need the top SIGNIFICAND_BITS + 1 bits, including the "implicit" one bit. To make rounding
     * easier, we pick out the top SIGNIFICAND_BITS + 2 bits, so we have one to help us round up or
     * down. twiceSignifFloor will contain the top SIGNIFICAND_BITS + 2 bits, and signifFloor the
     * top SIGNIFICAND_BITS + 1.
     *
     * It helps to consider the real number signif = absX * 2^(SIGNIFICAND_BITS - exponent).
     */
    int shi = exp2 - SIGNIFICAND_BITS - 1;
    long twice = abs2.shiftRight(shi).longValue();
    long signif = twice >> 1;
    signif &= SIGNIFICAND_MASK; // remove the implied bit

    /*
     * We round up if either the fractional part of signif is strictly greater than 0.5 (which is
     * true if the 0.5 bit is set and any lower bit is set), or if the fractional part of signif is
     * >= 0.5 and signifFloor is odd (which is true if both the 0.5 bit and the 1 bit are set).
     */
    boolean inc =
        (twice & 1) != 0 && ((signif & 1) != 0 || abs2.getLowestSetBit() < shi);
    long signif2 = inc ? signif + 1 : signif;
    long bit2 = (long) (exp2 + EXPONENT_BIAS) << SIGNIFICAND_BITS;
    bit2 += signif2;
    /*
     * If signifRounded == 2^53, we'd need to set all of the significand bits to zero and add 1 to
     * the exponent. This is exactly the behavior we get from just adding signifRounded to bits
     * directly. If the exponent is MAX_DOUBLE_EXPONENT, we round up (correctly) to
     * Double.POSITIVE_INFINITY.
     */
    bit2 |= x.signum() & SIGN_MASK;
    return longBitsToDouble(bit2);
  }

  /** Returns its argument if it is non-negative, zero if it is negative. */
  static double ensure(double val) {
    checkArgument(!isNaN(val));
    return max(val, 0.0);
  }

  @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L;
}
