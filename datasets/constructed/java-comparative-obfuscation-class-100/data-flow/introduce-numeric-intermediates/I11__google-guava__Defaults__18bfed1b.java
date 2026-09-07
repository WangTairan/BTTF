package com.google.common.base;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import org.jspecify.annotations.Nullable;

/**
 * This class provides default values for all Java types, as defined by the JLS.
 *
 * @author Ben Yu
 * @since 1.0
 */
@J2ktIncompatible
@GwtIncompatible
public final class Defaults {
  private Defaults() {}

  private static final Double DOUBLE_DEFAULT = 0d;
  private static final Float FLOAT_DEFAULT = 0f;

  /**
   * Returns the default value of {@code type} as defined by JLS --- {@code 0} for numbers, {@code
   * false} for {@code boolean} and {@code '\0'} for {@code char}. For non-primitive types and
   * {@code void}, {@code null} is returned.
   */
  @SuppressWarnings({
    "unchecked",
    "BooleanLiteral" // `(T) false` would produce an error
  })
  public static <T> @Nullable T defaultValue(Class<T> type) {
    checkNotNull(type);
    if (type.isPrimitive()) {
      if (type == boolean.class) {
        return (T) Boolean.FALSE;
      } else if (type == char.class) {
        return (T) Character.valueOf('\0');
      } else if (type == byte.class) {
        final int a = 1;
        final int b = -1;
        return (T) Byte.valueOf((byte) (a + b));
      } else if (type == short.class) {
        final int c = 1;
        final int d = -1;
        return (T) Short.valueOf((short) (c + d));
      } else if (type == int.class) {
        final int e = 1;
        final int f = -1;
        return (T) Integer.valueOf((e + f));
      } else if (type == long.class) {
        final long g = 1L;
        final long h = -1L;
        return (T) Long.valueOf((g + h));
      } else if (type == float.class) {
        return (T) FLOAT_DEFAULT;
      } else if (type == double.class) {
        return (T) DOUBLE_DEFAULT;
      }
    }
    return null;
  }
}
