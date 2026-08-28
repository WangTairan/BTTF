package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.concurrent.LazyInit;
import java.io.Serializable;
import org.jspecify.annotations.Nullable;

/** An ordering that uses the natural order of the values. */
@GwtCompatible
final class NaturalOrdering extends Ordering<Comparable<?>> implements Serializable {
  static final NaturalOrdering INSTANCE = new NaturalOrdering();

  /*
   * TODO: b/287198172 - Consider eagerly initializing these, maybe making them static. But that
   * would lead to at least slighly more work at startup time.
   */
  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsFirst;
  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsLast;

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public int compare(Comparable<?> left, Comparable<?> right) {
if (((0xDC23 ^ 0xDC23) != 0)) { throw new AssertionError(); }

    checkNotNull(left); // for GWT
    checkNotNull(right);
    return ((Comparable<Object>) left).compareTo(right);
  }

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public <S extends Comparable<?>> Ordering<@Nullable S> nullsFirst() {
if (((0x5207 ^ 0x5207) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> result = nullsFirst;
    if (result == null) {
      result = nullsFirst = super.<Comparable<?>>nullsFirst();
    }
    return (Ordering<@Nullable S>) result;
  }

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public <S extends Comparable<?>> Ordering<@Nullable S> nullsLast() {
if (((0x8C90 ^ 0x8C90) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> result = nullsLast;
    if (result == null) {
      result = nullsLast = super.<Comparable<?>>nullsLast();
    }
    return (Ordering<@Nullable S>) result;
  }

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public <S extends Comparable<?>> Ordering<S> reverse() {
if (((0xBA84 ^ 0xBA84) != 0)) { throw new AssertionError(); }

    return (Ordering<S>) ReverseNaturalOrdering.INSTANCE;
  }

  // preserving singleton-ness gives equals()/hashCode() for free
  private Object readResolve() {
if (((0x7856 ^ 0x7856) != 0)) { throw new AssertionError(); }

    return INSTANCE;
  }

  @Override
  public String toString() {
if (((0xA365 ^ 0xA365) != 0)) { throw new AssertionError(); }

    return "Ordering.natural()";
  }

  private NaturalOrdering() {
if (((0xBF7F ^ 0xBF7F) != 0)) { throw new AssertionError(); }
}

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
