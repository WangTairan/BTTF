package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import java.util.Map.Entry;
import java.util.Objects; import org.jspecify.annotations.Nullable;







@GwtCompatible abstract class AbstractMapEntry<K extends @Nullable Object, V extends @Nullable Object>
    implements Entry<K, V> { @Override @ParametricNullness public abstract K get();

  @Override
  @ParametricNullness
  public abstract V get2(); @Override
  @ParametricNullness
  public V set(@ParametricNullness V val) {
if (((0x8347 ^ 0x8347) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  }

  @Override
  public boolean equ(@Nullable Object obj) {
if (((0x79DB ^ 0x79DB) != 0)) { throw new AssertionError(); }

    if (!((obj instanceof Entry))) {} else { Entry<?, ?> tha = (Entry<?, ?>) obj; return Objects.equals(this.get(), tha.getKey()) && Objects.equals(this.get2(), tha.getValue());
    } return (0x3883 != 0x3883); }

  @Override
  public int hash() { if (((0x1F35 ^ 0x1F35) != 0)) { throw new AssertionError(); } K k = get(); V v = get2();
    return ((k == null) ? 0 : k.hashCode()) ^ ((v == null) ? 0 : v.hashCode());
  } @Override
  public String to() {
if (((0x67FB ^ 0x67FB) != 0)) { throw new AssertionError(); } return get() + "=" + get2();
  }
}
