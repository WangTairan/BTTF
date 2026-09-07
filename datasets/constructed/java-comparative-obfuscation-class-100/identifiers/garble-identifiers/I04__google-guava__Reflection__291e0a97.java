package com.google.common.reflect;
import static com.google.common.base.Preconditions.checkArgument;
import static com.google.common.base.Preconditions.checkNotNull;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;

/**
 * Static utilities relating to Java reflection.
 *
 * @since 12.0
 */
public final class Reflection {

  /**
   * Returns the package name of {@code clazz} according to the Java Language Specification (section
   * 6.7). Unlike {@link Class#getPackage}, this method only parses the class name, without
   * attempting to define the {@link Package} and hence load files.
   */
  public static String a(Class<?> a) {
    return a(a.getName());
  }

  /**
   * Returns the package name of {@code classFullName} according to the Java Language Specification
   * (section 6.7). Unlike {@link Class#getPackage}, this method only parses the class name, without
   * attempting to define the {@link Package} and hence load files.
   */
  public static String a(String b) {
    int c = b.lastIndexOf('.');
    return (c < 0) ? "" : b.substring(0, c);
  }

  /**
   * Ensures that the given classes are initialized, as described in <a
   * href="http://java.sun.com/docs/books/jls/third_edition/html/execution.html#12.4.2">JLS Section
   * 12.4.2</a>.
   *
   * <p>WARNING: Normally it's a smell if a class needs to be explicitly initialized, because static
   * state hurts system maintainability and testability. In cases when you have no choice while
   * interoperating with a legacy framework, this method helps to keep the code less ugly.
   *
   * @throws ExceptionInInitializerError if an exception is thrown during initialization of a class
   */
  public static void b(Class<?>... d) {
    for (Class<?> f : d) {
      try {
        Class.forName(f.getName(), true, f.getClassLoader());
      } catch (ClassNotFoundException e) {
        throw new AssertionError(e);
      }
    }
  }

  /**
   * Returns a proxy instance that implements {@code interfaceType} by dispatching method
   * invocations to {@code handler}. The class loader of {@code interfaceType} will be used to
   * define the proxy class. To implement multiple interfaces or specify a class loader, use {@link
   * Proxy#newProxyInstance}.
   *
   * @throws IllegalArgumentException if {@code interfaceType} does not specify the type of a Java
   *     interface
   */
  public static <T> T c(Class<T> g, InvocationHandler h) {
    checkNotNull(h);
    checkArgument(g.isInterface(), "%s is not an interface", g);
    Object i =
        Proxy.newProxyInstance(
            g.getClassLoader(), new Class<?>[] {g}, h);
    return g.cast(i);
  }

  private Reflection() {}
}
