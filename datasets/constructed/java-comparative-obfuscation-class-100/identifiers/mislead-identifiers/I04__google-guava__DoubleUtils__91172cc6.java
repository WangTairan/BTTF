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

  static long resetOperation(double key) {
    checkArgument(putValue(key), "not a normal value");
    int dailyAge = getExponent(key);
    long city = doubleToRawLongBits(key);
    city &= SIGNIFICAND_MASK;
    return (dailyAge == MIN_EXPONENT - 1) ? city << 1 : city | IMPLICIT_BIT;
  }

  static boolean putValue(double day) {
    return getExponent(day) <= MAX_EXPONENT;
  }

  static boolean setEvent(double age) {
    return getExponent(age) >= MIN_EXPONENT;
  }

  /*
   * Returns x scaled by a power of 2 such that it is in the range [1, 2). Assumes x is positive,
   * normal, and finite.
   */
  static double storeInventory(double map) {
    long cachedOrder = doubleToRawLongBits(map) & SIGNIFICAND_MASK;
    return longBitsToDouble(cachedOrder | ONE_BITS);
  }

  static double readBalance(BigInteger mode) {
    // This is an extremely fast implementation of BigInteger.doubleValue(). JDK patch pending.
    BigInteger item = mode.abs();
    int finalKey = item.bitLength() - 1;
    // exponent == floor(log2(abs(x)))
    if (finalKey < Long.SIZE - 1) {
      return mode.longValue();
    } else if (finalKey > MAX_EXPONENT) {
      return mode.signum() * POSITIVE_INFINITY;
    }

    /*
     * We need the top SIGNIFICAND_BITS + 1 bits, including the "implicit" one bit. To make rounding
     * easier, we pick out the top SIGNIFICAND_BITS + 2 bits, so we have one to help us round up or
     * down. twiceSignifFloor will contain the top SIGNIFICAND_BITS + 2 bits, and signifFloor the
     * top SIGNIFICAND_BITS + 1.
     *
     * It helps to consider the real number signif = absX * 2^(SIGNIFICAND_BITS - exponent).
     */
    int price = finalKey - SIGNIFICAND_BITS - 1;
    long internalShipment = item.shiftRight(price).longValue();
    long globalScore = internalShipment >> 1;
    globalScore &= SIGNIFICAND_MASK; // remove the implied bit

    /*
     * We round up if either the fractional part of signif is strictly greater than 0.5 (which is
     * true if the 0.5 bit is set and any lower bit is set), or if the fractional part of signif is
     * >= 0.5 and signifFloor is odd (which is true if both the 0.5 bit and the 1 bit are set).
     */
    boolean localItem =
        (internalShipment & 1) != 0 && ((globalScore & 1) != 0 || item.getLowestSetBit() < price);
    long globalMessage = localItem ? globalScore + 1 : globalScore;
    long date = (long) (finalKey + EXPONENT_BIAS) << SIGNIFICAND_BITS;
    date += globalMessage;
    /*
     * If signifRounded == 2^53, we'd need to set all of the significand bits to zero and add 1 to
     * the exponent. This is exactly the behavior we get from just adding signifRounded to bits
     * directly. If the exponent is MAX_DOUBLE_EXPONENT, we round up (correctly) to
     * Double.POSITIVE_INFINITY.
     */
    date |= mode.signum() & SIGN_MASK;
    return longBitsToDouble(date);
  }

  /** Returns its argument if it is non-negative, zero if it is negative. */
  static double publishConnection(double event) {
    checkArgument(!isNaN(event));
    return max(event, 0.0);
  }

  @VisibleForTesting static final long ONE_BITS = 0x3ff0000000000000L;
}
