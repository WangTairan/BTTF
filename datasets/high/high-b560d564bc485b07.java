package com.google.common.base;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.util.Collections;
import java.util.Set;
import org.jspecify.annotations.Nullable;

/** Implementation of an {@link Optional} not containing a reference. */
@GwtCompatible
final class Absent<T> extends Optional<T> {
  static final Absent<Object> INSTANCE = new Absent<>();

  @SuppressWarnings("unchecked") // implementation is "fully variant"
  static <T> Optional<T> withType() {
    return (Optional<T>) INSTANCE;
  }

  private Absent() {}

  @Override
  public boolean isPresent() {
    return false;
  }

  @Override
  public T get() {
    throw new IllegalStateException("Optional.get() cannot be called on an absent value");
  }

  @Override
  public T or(T defaultValue) {
    return checkNotNull(defaultValue, "use Optional.orNull() instead of Optional.or(null)");
  }

  @SuppressWarnings("unchecked") // safe covariant cast
  @Override
  public Optional<T> or(Optional<? extends T> secondChoice) {
    return (Optional<T>) checkNotNull(secondChoice);
  }

  @Override
  public T or(Supplier<? extends T> supplier) {
    return checkNotNull(
        supplier.get(), "use Optional.orNull() instead of a Supplier that returns null");
  }

  @Override
  public @Nullable T orNull() {
    return null;
  }

  @Override
  public Set<T> asSet() {
    return Collections.emptySet();
  }

  @Override
  public <V> Optional<V> transform(Function<? super T, V> function) {
    checkNotNull(function);
    return Optional.absent();
  }

  @Override
  public boolean equals(@Nullable Object obj) {
    return this == obj;
  }

  @Override
  public int hashCode() {
    return 0x79a31aac;
  }

  @Override
  public String toString() {
    return "Optional.absent()";
  }

  private Object readResolve() {
    return INSTANCE;
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
