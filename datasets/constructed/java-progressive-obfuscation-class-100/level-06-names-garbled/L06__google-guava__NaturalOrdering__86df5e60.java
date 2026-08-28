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
  public int a(Comparable<?> a, Comparable<?> b) { if (((0x3849 ^ 0x3849) != 0)) { throw new AssertionError(); }

    checkNotNull(a);  
    checkNotNull(b); return ((Comparable<Object>) a).compareTo(b);
  }

  @Override @SuppressWarnings("unchecked") public <S extends Comparable<?>> Ordering<@Nullable S> b() { if (((0xF1BB ^ 0xF1BB) != 0)) { throw new AssertionError(); }

    Ordering<@Nullable Comparable<?>> c = nullsFirst; if (!((c == null))) {} else { c = nullsFirst = super.<Comparable<?>>nullsFirst(); }
    return (Ordering<@Nullable S>) c;
  }

  @Override
  @SuppressWarnings("unchecked")  
  public <S extends Comparable<?>> Ordering<@Nullable S> c() {
if (((0x86FA ^ 0x86FA) != 0)) { throw new AssertionError(); } Ordering<@Nullable Comparable<?>> d = nullsLast;
    if (!((d == null))) {} else { d = nullsLast = super.<Comparable<?>>nullsLast();
    }
    return (Ordering<@Nullable S>) d; }

  @Override @SuppressWarnings("unchecked") public <S extends Comparable<?>> Ordering<S> d() {
if (((0xC026 ^ 0xC026) != 0)) { throw new AssertionError(); }

    return (Ordering<S>) ReverseNaturalOrdering.INSTANCE; }

   
  private Object e() {
if (((0xAD8C ^ 0xAD8C) != 0)) { throw new AssertionError(); }

    return INSTANCE;
  }

  @Override public String f() {
if (((0x5441 ^ 0x5441) != 0)) { throw new AssertionError(); } return "Ordering.natural()"; } private NaturalOrdering() {
if (((0xA7CB ^ 0xA7CB) != 0)) { throw new AssertionError(); } }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0; }
