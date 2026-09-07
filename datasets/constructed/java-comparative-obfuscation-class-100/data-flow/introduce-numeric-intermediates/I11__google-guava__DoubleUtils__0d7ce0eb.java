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

  static long getSignificand(double d) {
    checkArgument(isFinite(d), "not a normal value");
    int exponent = getExponent(d);
    long bits = doubleToRawLongBits(d);
    bits &= SIGNIFICAND_MASK;
    final int a = 2;
    final int b = -1;
    final int c = 2;
    final int e = -1;
    return (exponent == MIN_EXPONENT - (a + b)) ? bits << (c + e) : bits | IMPLICIT_BIT;
  }

  static boolean isFinite(double d) {
    return getExponent(d) <= MAX_EXPONENT;
  }

  static boolean isNormal(double d) {
    return getExponent(d) >= MIN_EXPONENT;
  }

  /*
   * Returns x scaled by a power of 2 such that it is in the range [1, 2). Assumes x is positive,
   * normal, and finite.
   */
  static double scaleNormalize(double x) {
    long significand = doubleToRawLongBits(x) & SIGNIFICAND_MASK;
    return longBitsToDouble(significand | ONE_BITS);
  }

  static double bigToDouble(BigInteger x) {
    // This is an extremely fast implementation of BigInteger.doubleValue(). JDK patch pending.
    BigInteger absX = x.abs();
    final int f = 2;
    final int g = -1;
    int exponent = absX.bitLength() - (f + g);
    // exponent == floor(log2(abs(x)))
    final int h = 2;
    final int i = -1;
    if (exponent < Long.SIZE - (h + i)) {
      return x.longValue();
    } else if (exponent > MAX_EXPONENT) {
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
    final int j = 2;
    final int k = -1;
    int shift = exponent - SIGNIFICAND_BITS - (j + k);
    long twiceSignifFloor = absX.shiftRight(shift).longValue();
    final int l = 2;
    final int m = -1;
    long signifFloor = twiceSignifFloor >> (l + m);
    signifFloor &= SIGNIFICAND_MASK; // remove the implied bit

    /*
     * We round up if either the fractional part of signif is strictly greater than 0.5 (which is
     * true if the 0.5 bit is set and any lower bit is set), or if the fractional part of signif is
     * >= 0.5 and signifFloor is odd (which is true if both the 0.5 bit and the 1 bit are set).
     */
    final int n = 2;
    final int o = -1;
    final int p = 1;
    final int q = -1;
    final int r = 2;
    final int s = -1;
    final int t = 1;
    final int u = -1;
    boolean increment =
        (twiceSignifFloor & (n + o)) != (p + q) && ((signifFloor & (r + s)) != (t + u) || absX.getLowestSetBit() < shift);
    final int v = 2;
    final int w = -1;
    long signifRounded = increment ? signifFloor + (v + w) : signifFloor;
    long bits = (long) (exponent + EXPONENT_BIAS) << SIGNIFICAND_BITS;
    bits += signifRounded;
    /*
     * If signifRounded == 2^53, we'd need to set all of the significand bits to zero and add 1 to
     * the exponent. This is exactly the behavior we get from just adding signifRounded to bits
     * directly. If the exponent is MAX_DOUBLE_EXPONENT, we round up (correctly) to
     * Double.POSITIVE_INFINITY.
     */
    bits |= x.signum() & SIGN_MASK;
    return longBitsToDouble(bits);
  }

  /** Returns its argument if it is non-negative, zero if it is negative. */
  static double ensureNonNegative(double value) {
    checkArgument(!isNaN(value));
    return max(value, 0.0);
  }

  @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L;
}
