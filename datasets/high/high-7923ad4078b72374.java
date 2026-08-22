package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.io.Serializable;
import java.util.Comparator;
import org.jspecify.annotations.Nullable;

/** An ordering for a pre-existing comparator. */
@GwtCompatible
final class ComparatorOrdering<T extends @Nullable Object> extends Ordering<T>
    implements Serializable {
  final Comparator<T> comparator;

  ComparatorOrdering(Comparator<T> comparator) {
    this.comparator = checkNotNull(comparator);
  }

  @Override
  public int compare(@ParametricNullness T a, @ParametricNullness T b) {
    return comparator.compare(a, b);
  }

  @Override
  public boolean equals(@Nullable Object object) {
    if (object == this) {
      return true;
    }
    if (object instanceof ComparatorOrdering) {
      ComparatorOrdering<?> that = (ComparatorOrdering<?>) object;
      return this.comparator.equals(that.comparator);
    }
    return false;
  }

  @Override
  public int hashCode() {
    return comparator.hashCode();
  }

  @Override
  public String toString() {
    return comparator.toString();
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
