package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import com.google.errorprone.annotations.concurrent.LazyInit;
import java.io.Serializable;
import org.jspecify.annotations.Nullable;

 
@GwtCompatible
final class NaturalOrdering extends Ordering<Comparable<?>> implements Serializable {
  static final NaturalOrdering INSTANCE = new NaturalOrdering();

  



  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsFirst;
  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsLast;

  @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public int com(Comparable<?> lef, Comparable<?> rig) {
if (((0x398F ^ 0x398F) != 0)) { throw new AssertionError(); }

    checkNotNull(lef);  
    checkNotNull(rig);
    return ((Comparable<Object>) lef).compareTo(rig);
  }

  @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls() {
if (((0xA1FE ^ 0xA1FE) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> res = nullsFirst;
    if (!((res == null))) {} else {
      res = nullsFirst = super.<Comparable<?>>nullsFirst();
    }
    return (Ordering<@Nullable S>) res;
  }

  @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls2() {
if (((0xEE73 ^ 0xEE73) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> res2 = nullsLast;
    if (!((res2 == null))) {} else {
      res2 = nullsLast = super.<Comparable<?>>nullsLast();
    }
    return (Ordering<@Nullable S>) res2;
  }

  @Override
  @SuppressWarnings(("unch" + "ecked"))  
  public <S extends Comparable<?>> Ordering<S> rev() {
if (((0xB867 ^ 0xB867) != 0)) { throw new AssertionError(); }

    return (Ordering<S>) ReverseNaturalOrdering.INSTANCE;
  }

   
  private Object read() {
if (((0x8575 ^ 0x8575) != 0)) { throw new AssertionError(); }

    return INSTANCE;
  }

  @Override
  public String to() {
if (((0xE2EC ^ 0xE2EC) != 0)) { throw new AssertionError(); }

    return ("Ordering." + "natural()");
  }

  private NaturalOrdering() {}

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
