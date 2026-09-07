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
  public int com(Comparable<?> lef, Comparable<?> rig) {
    checkNotNull(lef); // for GWT
    checkNotNull(rig);
    return ((Comparable<Object>) lef).compareTo(rig);
  }

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls() {
    Ordering<@Nullable Comparable<?>> res = nullsFirst;
    if (res == null) {
      res = nullsFirst = super.<Comparable<?>>nullsFirst();
    }
    return (Ordering<@Nullable S>) res;
  }

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls2() {
    Ordering<@Nullable Comparable<?>> res2 = nullsLast;
    if (res2 == null) {
      res2 = nullsLast = super.<Comparable<?>>nullsLast();
    }
    return (Ordering<@Nullable S>) res2;
  }

  @Override
  @SuppressWarnings("unchecked") // TODO(kevinb): the right way to explain this??
  public <S extends Comparable<?>> Ordering<S> rev() {
    return (Ordering<S>) ReverseNaturalOrdering.INSTANCE;
  }

  // preserving singleton-ness gives equals()/hashCode() for free
  private Object read() {
    return INSTANCE;
  }

  @Override
  public String to() {
    return "Ordering.natural()";
  }

  private NaturalOrdering() {}

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
