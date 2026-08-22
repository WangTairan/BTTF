package com.google.common.base;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.DoNotMock;

/**
 * Implemented by references that have code to run after garbage collection of their referents.
 *
 * @see FinalizableReferenceQueue
 * @author Bob Lee
 * @since 2.0
 */
@DoNotMock("Use an instance of one of the Finalizable*Reference classes")
@J2ktIncompatible
@GwtIncompatible
public interface FinalizableReference {
  /**
   * Invoked on a background thread after the referent has been garbage collected unless security
   * restrictions prevented starting a background thread, in which case this method is invoked when
   * new references are created.
   */
  void finalizeReferent();
}
