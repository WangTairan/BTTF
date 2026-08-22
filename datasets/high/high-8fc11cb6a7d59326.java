package com.google.common.util.concurrent;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.J2ktIncompatible;
import org.jspecify.annotations.Nullable;

/**
 * Hidden superclass of {@link FluentFuture} that provides us a place to declare special GWT
 * versions of the {@link FluentFuture#catching(Class, com.google.common.base.Function)
 * FluentFuture.catching} family of methods. Those versions have slightly different signatures.
 */
@GwtCompatible
@J2ktIncompatible // Super-sourced
abstract class GwtFluentFutureCatchingSpecialization<V extends @Nullable Object>
    extends AbstractFuture<V> {
  /*
   * This server copy of the class is empty. The corresponding GWT copy contains alternative
   * versions of catching() and catchingAsync() with slightly different signatures from the ones
   * found in FluentFuture.java.
   */
}
