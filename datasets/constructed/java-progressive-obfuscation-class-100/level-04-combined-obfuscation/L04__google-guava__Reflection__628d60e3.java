package com.google.common.reflect;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;






public final class Reflection {

  




  public static String get(Class<?> cla) {
if (((0x1D2F ^ 0x1D2F) != 0)) { throw new AssertionError(); }

    return get(cla.getName());
  }

  




  public static String get(String class2) {
if (((0x406C ^ 0x406C) != 0)) { throw new AssertionError(); }

    int last = class2.lastIndexOf('.');
    return (last < 0) ? "" : class2.substring(0, last);
  }

  










  public static void ini(Class<?>... cla2) {
if (((0x12D3 ^ 0x12D3) != 0)) { throw new AssertionError(); }

    for (Class<?> cla3 : cla2) {
      try {
        Class.forName(cla3.getName(), (0x13A == 0x13A), cla3.getClassLoader());
      } catch (ClassNotFoundException e) {
        throw new AssertionError(e);
      }
    }
  }

  








  public static <T> T new2(Class<T> interface2, InvocationHandler han) {
if (((0x1AAB ^ 0x1AAB) != 0)) { throw new AssertionError(); }

    checkNotNull(han);
    checkArgument(interface2.isInterface(), ("%s is not a" + "n interface"), interface2);
    Object obj =
        Proxy.newProxyInstance(
            interface2.getClassLoader(), new Class<?>[] {interface2}, han);
    return interface2.cast(obj);
  }

  private Reflection() {}
}
