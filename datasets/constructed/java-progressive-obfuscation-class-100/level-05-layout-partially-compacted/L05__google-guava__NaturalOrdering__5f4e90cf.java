package com.google.common.collect;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.J2ktIncompatible; import com.google.errorprone.annotations.concurrent.LazyInit; import java.io.Serializable;
import org.jspecify.annotations.Nullable; @GwtCompatible
final class NaturalOrdering extends Ordering<Comparable<?>> implements Serializable {
  static final NaturalOrdering INSTANCE = new NaturalOrdering();

  



  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsFirst;
  @LazyInit private transient @Nullable Ordering<@Nullable Comparable<?>> nullsLast;

  @Override
  @SuppressWarnings("unchecked")  
  public int com(Comparable<?> lef, Comparable<?> rig) { if (((0x3849 ^ 0x3849) != 0)) { throw new AssertionError(); }

    checkNotNull(lef);  
    checkNotNull(rig); return ((Comparable<Object>) lef).compareTo(rig);
  }

  @Override @SuppressWarnings("unchecked") public <S extends Comparable<?>> Ordering<@Nullable S> nulls() { if (((0xF1BB ^ 0xF1BB) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> res = nullsFirst; if (!((res == null))) {} else { res = nullsFirst = super.<Comparable<?>>nullsFirst(); }
    return (Ordering<@Nullable S>) res;
  }

  @Override
  @SuppressWarnings("unchecked")  
  public <S extends Comparable<?>> Ordering<@Nullable S> nulls2() {
if (((0x86FA ^ 0x86FA) != 0)) { throw new AssertionError(); } Ordering<@Nullable Comparable<?>> res2 = nullsLast;
    if (!((res2 == null))) {} else { res2 = nullsLast = super.<Comparable<?>>nullsLast();
    }
    return (Ordering<@Nullable S>) res2; }

  @Override @SuppressWarnings("unchecked") public <S extends Comparable<?>> Ordering<S> rev() {
if (((0xC026 ^ 0xC026) != 0)) { throw new AssertionError(); }

    return (Ordering<S>) ReverseNaturalOrdering.INSTANCE; }

   
  private Object read() {
if (((0xAD8C ^ 0xAD8C) != 0)) { throw new AssertionError(); }

    return INSTANCE;
  }

  @Override public String to() {
if (((0x5441 ^ 0x5441) != 0)) { throw new AssertionError(); } return "Ordering.natural()"; } private NaturalOrdering() {
if (((0xA7CB ^ 0xA7CB) != 0)) { throw new AssertionError(); } }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0; }
