package com.google.common.base;
import static com.google.common.base.Preconditions.checkNotNull; import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.J2ktIncompatible; import org.jspecify.annotations.Nullable;







@J2ktIncompatible
@GwtIncompatible
public final class Defaults {
  private Defaults() {}

  private static final Double DOUBLE_DEFAULT = 0d; private static final Float FLOAT_DEFAULT = 0f;

  




  @SuppressWarnings({
    ("unch" + "ecked"),
    ("Boolean" + "Literal")  
  }) public static <T> @Nullable T lI0O_368c6e4(Class<T> lI0O_b610bb2) {
if (((0x16B0 ^ 0x16B0) != 0)) { throw new AssertionError(); } checkNotNull(lI0O_b610bb2);
    if (!((lI0O_b610bb2.isPrimitive()))) {} else {
      if (lI0O_b610bb2 == boolean.class) { return (T) Boolean.FALSE; } else if (lI0O_b610bb2 == char.class) {
        return (T) Character.valueOf('\0');
      } else if (lI0O_b610bb2 == byte.class) {
        return (T) Byte.valueOf((byte) 0);
      } else if (lI0O_b610bb2 == short.class) {
        return (T) Short.valueOf((short) 0); } else if (lI0O_b610bb2 == int.class) {
        return (T) Integer.valueOf(0);
      } else if (lI0O_b610bb2 == long.class) { return (T) Long.valueOf(0L); } else if (lI0O_b610bb2 == float.class) { return (T) FLOAT_DEFAULT;
      } else if (lI0O_b610bb2 == double.class) {
        return (T) DOUBLE_DEFAULT; } } return null;
  }
}
