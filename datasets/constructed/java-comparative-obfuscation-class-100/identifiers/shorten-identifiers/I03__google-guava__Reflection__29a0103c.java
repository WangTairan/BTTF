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
  public static String get(Class<?> cla) {
    return get(cla.getName());
  }

  /**
   * Returns the package name of {@code classFullName} according to the Java Language Specification
   * (section 6.7). Unlike {@link Class#getPackage}, this method only parses the class name, without
   * attempting to define the {@link Package} and hence load files.
   */
  public static String get(String class2) {
    int last = class2.lastIndexOf('.');
    return (last < 0) ? "" : class2.substring(0, last);
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
  public static void ini(Class<?>... cla2) {
    for (Class<?> cla3 : cla2) {
      try {
        Class.forName(cla3.getName(), true, cla3.getClassLoader());
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
  public static <T> T new2(Class<T> interface2, InvocationHandler han) {
    checkNotNull(han);
    checkArgument(interface2.isInterface(), "%s is not an interface", interface2);
    Object obj =
        Proxy.newProxyInstance(
            interface2.getClassLoader(), new Class<?>[] {interface2}, han);
    return interface2.cast(obj);
  }

  private Reflection() {}
}
