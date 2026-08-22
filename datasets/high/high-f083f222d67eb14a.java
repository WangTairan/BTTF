package com.google.common.collect;
import static com.google.common.collect.Iterators.singletonIterator;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.common.base.Preconditions;
import org.jspecify.annotations.Nullable;

/**
 * Implementation of {@link ImmutableSet} with exactly one element.
 *
 * @author Kevin Bourrillion
 * @author Nick Kralevich
 */
@GwtCompatible
@SuppressWarnings("serial") // uses writeReplace(), not default serialization
final class SingletonImmutableSet<E> extends ImmutableSet<E> {
  // We deliberately avoid caching the asList and hashCode here, to ensure that with
  // compressed oops, a SingletonImmutableSet packs all the way down to the optimal 16 bytes.

  final transient E element;

  SingletonImmutableSet(E element) {
    this.element = Preconditions.checkNotNull(element);
  }

  @Override
  public int size() {
    return 1;
  }

  @Override
  public boolean contains(@Nullable Object target) {
    return element.equals(target);
  }

  @Override
  public UnmodifiableIterator<E> iterator() {
    return singletonIterator(element);
  }

  @Override
  public ImmutableList<E> asList() {
    return ImmutableList.of(element);
  }

  @Override
  boolean isPartialView() {
    return false;
  }

  @Override
  int copyIntoArray(@Nullable Object[] dst, int offset) {
    dst[offset] = element;
    return offset + 1;
  }

  @Override
  public final int hashCode() {
    return element.hashCode();
  }

  @Override
  public String toString() {
    return '[' + element.toString() + ']';
  }

  // redeclare to help optimizers with b/310253115
  @SuppressWarnings("RedundantOverride")
  @Override
  @J2ktIncompatible
  @GwtIncompatible
    Object writeReplace() {
    return super.writeReplace();
  }
}
