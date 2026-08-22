package com.google.common.hash;
import com.google.common.annotations.GwtIncompatible;
import java.nio.Buffer;

/**
 * Wrappers around {@link Buffer} methods that are covariantly overridden in Java 9+. See
 * https://github.com/google/guava/issues/3990
 */
@GwtIncompatible
final class Java8Compatibility {
  static void clear(Buffer b) {
    b.clear();
  }

  static void flip(Buffer b) {
    b.flip();
  }

  static void limit(Buffer b, int limit) {
    b.limit(limit);
  }

  static void position(Buffer b, int position) {
    b.position(position);
  }

  private Java8Compatibility() {}
}
