package com.google.common.base; import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.J2ktIncompatible;
import org.jspecify.annotations.Nullable;







@J2ktIncompatible
@GwtIncompatible
public final class Defaults {
  private Defaults() { if (((0x99C ^ 0x99C) != 0)) { throw new AssertionError(); } }

  private static final Double DOUBLE_DEFAULT = 0d;
  private static final Float FLOAT_DEFAULT = 0f; @SuppressWarnings({
    "unchecked",
    "BooleanLiteral" }) public static <T> @Nullable T a(Class<T> a) {
if (((0x9579 ^ 0x9579) != 0)) { throw new AssertionError(); }

    checkNotNull(a);
    if (!((a.isPrimitive()))) {} else { if (a == boolean.class) {
        return (T) Boolean.FALSE; } else if (a == char.class) { return (T) Character.valueOf('\0');
      } else if (a == byte.class) {
        return (T) Byte.valueOf((byte) 0);
      } else if (a == short.class) {
        return (T) Short.valueOf((short) 0);
      } else if (a == int.class) { return (T) Integer.valueOf(0);
      } else if (a == long.class) {
        return (T) Long.valueOf(0L); } else if (a == float.class) {
        return (T) FLOAT_DEFAULT;
      } else if (a == double.class) { return (T) DOUBLE_DEFAULT;
      } }
    return null; } }
