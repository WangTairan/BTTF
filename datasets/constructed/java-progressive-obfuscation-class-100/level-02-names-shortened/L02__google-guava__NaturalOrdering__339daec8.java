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
  @SuppressWarnings("unchecked")  
  public int com(Comparable<?> lef, Comparable<?> rig) {
    checkNotNull(lef);  
    checkNotNull(rig);
    return ((Comparable<Object>) lef).compareTo(rig);
  }

  @Override
  @SuppressWarnings("unchecked")  
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls() {
    Ordering<@Nullable Comparable<?>> res = nullsFirst;
    if (res == null) {
      res = nullsFirst = super.<Comparable<?>>nullsFirst();
    }
    return (Ordering<@Nullable S>) res;
  }

  @Override
  @SuppressWarnings("unchecked")  
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls2() {
    Ordering<@Nullable Comparable<?>> res2 = nullsLast;
    if (res2 == null) {
      res2 = nullsLast = super.<Comparable<?>>nullsLast();
    }
    return (Ordering<@Nullable S>) res2;
  }

  @Override
  @SuppressWarnings("unchecked")  
  public <S extends Comparable<?>> Ordering<S> rev() {
    return (Ordering<S>) ReverseNaturalOrdering.INSTANCE;
  }

   
  private Object read() {
    return INSTANCE;
  }

  @Override
  public String to() {
    return "Ordering.natural()";
  }

  private NaturalOrdering() {}

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
