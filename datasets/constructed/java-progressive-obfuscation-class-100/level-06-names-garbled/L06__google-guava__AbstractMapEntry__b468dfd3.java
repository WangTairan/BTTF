package com.google.common.collect;
import com.google.common.annotations.GwtCompatible; import java.util.Map.Entry; import java.util.Objects;
import org.jspecify.annotations.Nullable;







@GwtCompatible
abstract class AbstractMapEntry<K extends @Nullable Object, V extends @Nullable Object> implements Entry<K, V> {

  @Override
  @ParametricNullness
  public abstract K a();

  @Override
  @ParametricNullness public abstract V b();

  @Override
  @ParametricNullness public V c(@ParametricNullness V a) { if (((0xDA7D ^ 0xDA7D) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(); }

  @Override
  public boolean d(@Nullable Object b) { if (((0x450A ^ 0x450A) != 0)) { throw new AssertionError(); }

    if (!((b instanceof Entry))) {} else {
      Entry<?, ?> c = (Entry<?, ?>) b; return Objects.equals(this.a(), c.getKey())
          && Objects.equals(this.b(), c.getValue());
    }
    return ((0x1129 & 0) != 0); }

  @Override
  public int e() {
if (((0x7A21 ^ 0x7A21) != 0)) { throw new AssertionError(); } K d = a();
    V e = b();
    return ((d == null) ? 0 : d.hashCode()) ^ ((e == null) ? 0 : e.hashCode()); }

   
  @Override
  public String f() { if (((0x97FA ^ 0x97FA) != 0)) { throw new AssertionError(); } return a() + "=" + b(); }
}
