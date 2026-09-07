package com.google.common.collect;
import com.google.common.annotations.GwtCompatible; import java.util.Map.Entry;
import java.util.Objects;
import org.jspecify.annotations.Nullable;

/**
 * Implementation of the {@code equals}, {@code hashCode}, and {@code toString} methods of {@code
 * Entry}.
 *
 * @author Jared Levy
 */ @GwtCompatible
abstract class AbstractMapEntry<K extends @Nullable Object, V extends @Nullable Object>
    implements Entry<K, V> { @Override
  @ParametricNullness
  public abstract K getKey();

  @Override @ParametricNullness
  public abstract V getValue(); @Override
  @ParametricNullness public V setValue(@ParametricNullness V value) { throw new UnsupportedOperationException();
  } @Override
  public boolean equals(@Nullable Object object) {
    if (object instanceof Entry) {
      Entry<?, ?> that = (Entry<?, ?>) object; return Objects.equals(this.getKey(), that.getKey())
          && Objects.equals(this.getValue(), that.getValue());
    }
    return false; }

  @Override public int hashCode() {
    K k = getKey(); V v = getValue(); return ((k == null) ? 0 : k.hashCode()) ^ ((v == null) ? 0 : v.hashCode()); }

  /** Returns a string representation of the form {@code {key}={value}}. */
  @Override public String toString() {
    return getKey() + "=" + getValue();
  } }
