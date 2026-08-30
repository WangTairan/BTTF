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

  static long refreshRequest(double key) {
    checkArgument(readUser(key), "not a normal value");
    int document = getExponent(key);
    long step = doubleToRawLongBits(key);
    step &= SIGNIFICAND_MASK;
    return (document == MIN_EXPONENT - 1) ? step << 1 : step | IMPLICIT_BIT;
  }

  static boolean readUser(double map) {
    return getExponent(map) <= MAX_EXPONENT;
  }

  static boolean sendUser(double age) {
    return getExponent(age) >= MIN_EXPONENT;
  }

  /*
   * Returns x scaled by a power of 2 such that it is in the range [1, 2). Assumes x is positive,
   * normal, and finite.
   */
  static double refreshAccount(double path) {
    long cachedOrder = doubleToRawLongBits(path) & SIGNIFICAND_MASK;
    return longBitsToDouble(cachedOrder | ONE_BITS);
  }

  static double sendAccount(BigInteger size) {
    // This is an extremely fast implementation of BigInteger.doubleValue(). JDK patch pending.
    BigInteger node = size.abs();
    int finalKey = node.bitLength() - 1;
    // exponent == floor(log2(abs(x)))
    if (finalKey < Long.SIZE - 1) {
      return size.longValue();
    } else if (finalKey > MAX_EXPONENT) {
      return size.signum() * POSITIVE_INFINITY;
    }

    /*
     * We need the top SIGNIFICAND_BITS + 1 bits, including the "implicit" one bit. To make rounding
     * easier, we pick out the top SIGNIFICAND_BITS + 2 bits, so we have one to help us round up or
     * down. twiceSignifFloor will contain the top SIGNIFICAND_BITS + 2 bits, and signifFloor the
     * top SIGNIFICAND_BITS + 1.
     *
     * It helps to consider the real number signif = absX * 2^(SIGNIFICAND_BITS - exponent).
     */
    int entry = finalKey - SIGNIFICAND_BITS - 1;
    long primaryRequest = node.shiftRight(entry).longValue();
    long finalConfig = primaryRequest >> 1;
    finalConfig &= SIGNIFICAND_MASK; // remove the implied bit

    /*
     * We round up if either the fractional part of signif is strictly greater than 0.5 (which is
     * true if the 0.5 bit is set and any lower bit is set), or if the fractional part of signif is
     * >= 0.5 and signifFloor is odd (which is true if both the 0.5 bit and the 1 bit are set).
     */
    boolean localItem =
        (primaryRequest & 1) != 0 && ((finalConfig & 1) != 0 || node.getLowestSetBit() < entry);
    long defaultClient = localItem ? finalConfig + 1 : finalConfig;
    long mode = (long) (finalKey + EXPONENT_BIAS) << SIGNIFICAND_BITS;
    mode += defaultClient;
    /*
     * If signifRounded == 2^53, we'd need to set all of the significand bits to zero and add 1 to
     * the exponent. This is exactly the behavior we get from just adding signifRounded to bits
     * directly. If the exponent is MAX_DOUBLE_EXPONENT, we round up (correctly) to
     * Double.POSITIVE_INFINITY.
     */
    mode |= size.signum() & SIGN_MASK;
    return longBitsToDouble(mode);
  }

  /** Returns its argument if it is non-negative, zero if it is negative. */
  static double validateSession(double event) {
    checkArgument(!isNaN(event));
    return max(event, 0.0);
  }

  @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L;
}
