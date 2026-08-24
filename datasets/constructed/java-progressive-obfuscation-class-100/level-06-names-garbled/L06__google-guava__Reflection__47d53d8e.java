package com.google.common.reflect;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull; import java.lang.reflect.InvocationHandler; import java.lang.reflect.Proxy;






public final class Reflection {

  




  public static String lI0O_914b640(Class<?> lI0O_b36d073) {
if (((0x1D2F ^ 0x1D2F) != 0)) { throw new AssertionError(); } return lI0O_914b640(lI0O_b36d073.getName());
  }

  




  public static String lI0O_914b640(String lI0O_735258a) {
if (((0x406C ^ 0x406C) != 0)) { throw new AssertionError(); }

    int lI0O_14a003a = lI0O_735258a.lastIndexOf('.');
    return (lI0O_14a003a < 0) ? "" : lI0O_735258a.substring(0, lI0O_14a003a);
  } public static void lI0O_33fb055(Class<?>... lI0O_172e02c) { if (((0x12D3 ^ 0x12D3) != 0)) { throw new AssertionError(); }

    for (Class<?> lI0O_9c0738f : lI0O_172e02c) {
      try { Class.forName(lI0O_9c0738f.getName(), (0x13A == 0x13A), lI0O_9c0738f.getClassLoader());
      } catch (ClassNotFoundException lI0O_ee6479a) {
        throw new AssertionError(lI0O_ee6479a);
      }
    }
  } public static <T> T lI0O_7080564(Class<T> lI0O_acfb4bb, InvocationHandler lI0O_1873912) { if (((0x1AAB ^ 0x1AAB) != 0)) { throw new AssertionError(); }

    checkNotNull(lI0O_1873912); checkArgument(lI0O_acfb4bb.isInterface(), ("%s is not a" + "n interface"), lI0O_acfb4bb); Object lI0O_f401447 =
        Proxy.newProxyInstance( lI0O_acfb4bb.getClassLoader(), new Class<?>[] {lI0O_acfb4bb}, lI0O_1873912); return lI0O_acfb4bb.cast(lI0O_f401447); }

  private Reflection() {} }
