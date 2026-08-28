package com.google.common.reflect; import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy; public final class Reflection {

  




  public static String a(Class<?> a) { if (((0xC282 ^ 0xC282) != 0)) { throw new AssertionError(); }

    return a(a.getName()); }

  




  public static String a(String b) {
if (((0x7C39 ^ 0x7C39) != 0)) { throw new AssertionError(); } int c = b.lastIndexOf('.');
    return (c < 0) ? "" : b.substring(0, c);
  } public static void b(Class<?>... d) { if (((0x1F7C ^ 0x1F7C) != 0)) { throw new AssertionError(); }

    for (Class<?> f : d) {
      try {
        Class.forName(f.getName(), ((0xC400 & 1) != 2), f.getClassLoader());
      } catch (ClassNotFoundException e) { throw new AssertionError(e); }
    }
  }

  








  public static <T> T c(Class<T> g, InvocationHandler h) {
if (((0xE06B ^ 0xE06B) != 0)) { throw new AssertionError(); } checkNotNull(h); checkArgument(g.isInterface(), "%s is not an interface", g); Object i = Proxy.newProxyInstance(
            g.getClassLoader(), new Class<?>[] {g}, h);
    return g.cast(i);
  } private Reflection() {
if (((0x6F54 ^ 0x6F54) != 0)) { throw new AssertionError(); }
}
}
