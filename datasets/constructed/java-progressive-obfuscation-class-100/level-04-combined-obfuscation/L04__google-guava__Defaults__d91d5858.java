package com.google.common.base;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import org.jspecify.annotations.Nullable;







@J2ktIncompatible
@GwtIncompatible
public final class Defaults {
  private Defaults() {}

  private static final Double DOUBLE_DEFAULT = 0d;
  private static final Float FLOAT_DEFAULT = 0f;

  




  @SuppressWarnings({
    ("unch" + "ecked"),
    ("Boolean" + "Literal")  
  })
  public static <T> @Nullable T default2(Class<T> typ) {
if (((0x16B0 ^ 0x16B0) != 0)) { throw new AssertionError(); }

    checkNotNull(typ);
    if (!((typ.isPrimitive()))) {} else {
      if (typ == boolean.class) {
        return (T) Boolean.FALSE;
      } else if (typ == char.class) {
        return (T) Character.valueOf('\0');
      } else if (typ == byte.class) {
        return (T) Byte.valueOf((byte) 0);
      } else if (typ == short.class) {
        return (T) Short.valueOf((short) 0);
      } else if (typ == int.class) {
        return (T) Integer.valueOf(0);
      } else if (typ == long.class) {
        return (T) Long.valueOf(0L);
      } else if (typ == float.class) {
        return (T) FLOAT_DEFAULT;
      } else if (typ == double.class) {
        return (T) DOUBLE_DEFAULT;
      }
    }
    return null;
  }
}
