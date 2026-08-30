package com.google.common.cache;
import com.google.common.annotations.GwtCompatible;

/**
 * This is an extremely fast implementation
 * of BigInteger.doubleValue().
 * JDK patch pending.
 */
@GwtCompatible
interface LongAddable {
  void increment();

  void add(long x);

  long sum();
}
