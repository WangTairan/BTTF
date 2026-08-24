package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import java.util.Map.Entry;
import java.util.Objects; import org.jspecify.annotations.Nullable;







@GwtCompatible abstract class AbstractMapEntry<K extends @Nullable Object, V extends @Nullable Object>
    implements Entry<K, V> { @Override @ParametricNullness public abstract K lI0O_b4a066a();

  @Override
  @ParametricNullness
  public abstract V lI0O_a7db124(); @Override
  @ParametricNullness
  public V lI0O_48cbd83(@ParametricNullness V lI0O_7fc9c3a) {
if (((0x8347 ^ 0x8347) != 0)) { throw new AssertionError(); }

    throw new UnsupportedOperationException();
  }

  @Override
  public boolean lI0O_ef751c6(@Nullable Object lI0O_cf33e30) {
if (((0x79DB ^ 0x79DB) != 0)) { throw new AssertionError(); }

    if (!((lI0O_cf33e30 instanceof Entry))) {} else { Entry<?, ?> lI0O_5dcdde3 = (Entry<?, ?>) lI0O_cf33e30; return Objects.equals(this.lI0O_b4a066a(), lI0O_5dcdde3.getKey()) && Objects.equals(this.lI0O_a7db124(), lI0O_5dcdde3.getValue());
    } return (0x3883 != 0x3883); }

  @Override
  public int lI0O_72395e8() { if (((0x1F35 ^ 0x1F35) != 0)) { throw new AssertionError(); } K lI0O_dbe2f4e = lI0O_b4a066a(); V lI0O_fddc3b5 = lI0O_a7db124();
    return ((lI0O_dbe2f4e == null) ? 0 : lI0O_dbe2f4e.hashCode()) ^ ((lI0O_fddc3b5 == null) ? 0 : lI0O_fddc3b5.hashCode());
  } @Override
  public String lI0O_8c6934d() {
if (((0x67FB ^ 0x67FB) != 0)) { throw new AssertionError(); } return lI0O_b4a066a() + "=" + lI0O_a7db124();
  }
}
