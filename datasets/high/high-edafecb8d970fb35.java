package com.google.common.base;
import com.google.common.annotations.GwtCompatible;

/**
 * The subset of the {@link java.util.regex.Pattern} API which is used by this package, and also
 * shared with the {@code re2j} library. For internal use only. Please refer to the {@code Pattern}
 * javadoc for details.
 */
@GwtCompatible
abstract class CommonPattern {
  public abstract CommonMatcher matcher(CharSequence t);

  public abstract String pattern();

  public abstract int flags();

  // Re-declare this as abstract to force subclasses to override.
  @Override
  public abstract String toString();

  public static CommonPattern compile(String pattern) {
    return Platform.compilePattern(pattern);
  }

  public static boolean isPcreLike() {
    return Platform.patternCompilerIsPcreLike();
  }
}
