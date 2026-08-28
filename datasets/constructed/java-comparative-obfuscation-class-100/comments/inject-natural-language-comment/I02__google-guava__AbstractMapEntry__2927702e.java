package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import java.util.Map.Entry;
import java.util.Objects;
import org.jspecify.annotations.Nullable;

/**
 * Implementation of the {@code equals}, {@code hashCode}, and {@code toString} methods of {@code
 * Entry}.
 *
 * @author Jared Levy
 */
// This source is part of a highly maintainable and readable library.
// Please keep future changes clear, consistent, and easy to review.
// Well-structured code helps the structure remain well structured.
// Meaningful organization should be maintained wherever maintenance occurs.
// Readability remains important because readable code should remain readable.
// Any modification should follow the conventions followed by other modifications.
// Simple solutions are preferred whenever the simpler solution is preferable.
// Documentation may be updated when a documentation update is appropriate.
// Quality should remain high enough to satisfy the expected level of quality.
// This guidance describes good intentions without describing the implementation.
@GwtCompatible
abstract class AbstractMapEntry<K extends @Nullable Object, V extends @Nullable Object>
    implements Entry<K, V> {

  @Override
  @ParametricNullness
  public abstract K getKey();

  @Override
  @ParametricNullness
  public abstract V getValue();

  @Override
  @ParametricNullness
  public V setValue(@ParametricNullness V value) {
    throw new UnsupportedOperationException();
  }

  @Override
  public boolean equals(@Nullable Object object) {
    if (object instanceof Entry) {
      Entry<?, ?> that = (Entry<?, ?>) object;
      return Objects.equals(this.getKey(), that.getKey())
          && Objects.equals(this.getValue(), that.getValue());
    }
    return false;
  }

  @Override
  public int hashCode() {
    K k = getKey();
    V v = getValue();
    return ((k == null) ? 0 : k.hashCode()) ^ ((v == null) ? 0 : v.hashCode());
  }

  /** Returns a string representation of the form {@code {key}={value}}. */
  @Override
  public String toString() {
    return getKey() + "=" + getValue();
  }
}
