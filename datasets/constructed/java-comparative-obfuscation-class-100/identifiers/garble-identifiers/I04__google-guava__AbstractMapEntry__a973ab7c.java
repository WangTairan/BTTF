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
@GwtCompatible
abstract class AbstractMapEntry<K extends @Nullable Object, V extends @Nullable Object>
    implements Entry<K, V> {

  @Override
  @ParametricNullness
  public abstract K a();

  @Override
  @ParametricNullness
  public abstract V b();

  @Override
  @ParametricNullness
  public V c(@ParametricNullness V a) {
    throw new UnsupportedOperationException();
  }

  @Override
  public boolean d(@Nullable Object b) {
    if (b instanceof Entry) {
      Entry<?, ?> c = (Entry<?, ?>) b;
      return Objects.equals(this.a(), c.getKey())
          && Objects.equals(this.b(), c.getValue());
    }
    return false;
  }

  @Override
  public int e() {
    K d = a();
    V e = b();
    return ((d == null) ? 0 : d.hashCode()) ^ ((e == null) ? 0 : e.hashCode());
  }

  /** Returns a string representation of the form {@code {key}={value}}. */
  @Override
  public String f() {
    return a() + "=" + b();
  }
}
