package com.google.common.collect; import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import com.google.errorprone.annotations.concurrent.LazyInit; import java.io.Serializable; import org.jspecify.annotations.Nullable;

 
@GwtCompatible
final class NaturalOrdering extends Ordering<Comparable<?>> implements Serializable {
  static final NaturalOrdering INSTANCE = new NaturalOrdering();

  



  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsFirst;
  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsLast; @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public int lI0O_2b5932f(Comparable<?> lI0O_4dbc031, Comparable<?> lI0O_2e51d89) {
if (((0x398F ^ 0x398F) != 0)) { throw new AssertionError(); } checkNotNull(lI0O_4dbc031);  
    checkNotNull(lI0O_2e51d89); return ((Comparable<Object>) lI0O_4dbc031).compareTo(lI0O_2e51d89);
  }

  @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public <S extends Comparable<?>> Ordering<@Nullable S> lI0O_66ebd4d() {
if (((0xA1FE ^ 0xA1FE) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> lI0O_ae6f63e = nullsFirst; if (!((lI0O_ae6f63e == null))) {} else {
      lI0O_ae6f63e = nullsFirst = super.<Comparable<?>>nullsFirst(); }
    return (Ordering<@Nullable S>) lI0O_ae6f63e;
  }

  @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public <S extends Comparable<?>> Ordering<@Nullable S> lI0O_6f20cda() {
if (((0xEE73 ^ 0xEE73) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> lI0O_443e785 = nullsLast;
    if (!((lI0O_443e785 == null))) {} else {
      lI0O_443e785 = nullsLast = super.<Comparable<?>>nullsLast();
    } return (Ordering<@Nullable S>) lI0O_443e785; } @Override @SuppressWarnings(("unch" + "ecked")) public <S extends Comparable<?>> Ordering<S> lI0O_97d3c45() {
if (((0xB867 ^ 0xB867) != 0)) { throw new AssertionError(); } return (Ordering<S>) ReverseNaturalOrdering.INSTANCE; } private Object lI0O_045bdc4() { if (((0x8575 ^ 0x8575) != 0)) { throw new AssertionError(); } return INSTANCE; } @Override public String lI0O_33b9a28() {
if (((0xE2EC ^ 0xE2EC) != 0)) { throw new AssertionError(); } return ("Ordering." + "natural()");
  }

  private NaturalOrdering() {}

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
