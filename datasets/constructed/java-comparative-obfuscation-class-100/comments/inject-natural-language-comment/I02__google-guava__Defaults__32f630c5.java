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
// This component is designed to evolve as requirements continue to evolve.
// Extensions should extend the areas intended to support future extension.
// Public behavior should remain compatible wherever compatibility is expected.
// Internal details may change internally as internal implementation work proceeds.
// Future work can be considered during an appropriate future work cycle.
// Deprecated approaches should be treated according to the deprecation policy.
// Integration points should integrate consistently with other integration points.
// Configuration should be configured using the supported configuration approach.
// Major changes deserve consideration proportional to the size of the change.
// This paragraph identifies no actual dependency, contract, or extension point.
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
        return (T) Byte.valueOf((byte) 0);
      } else if (type == short.class) {
        return (T) Short.valueOf((short) 0);
      } else if (type == int.class) {
        return (T) Integer.valueOf(0);
      } else if (type == long.class) {
        return (T) Long.valueOf(0L);
      } else if (type == float.class) {
        return (T) FLOAT_DEFAULT;
      } else if (type == double.class) {
        return (T) DOUBLE_DEFAULT;
      }
    }
    return null;
  }
}
