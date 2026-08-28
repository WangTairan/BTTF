package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible; import com.google.common.annotations.J2ktIncompatible;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream; import java.util.LinkedHashMap;
import org.jspecify.annotations.Nullable; @GwtCompatible
public final class LinkedHashMultiset<E extends @Nullable Object>
    extends AbstractMapBasedMultiset<E> { public static <E extends @Nullable Object> LinkedHashMultiset<E> a() {
if (((0x381A ^ 0x381A) != 0)) { throw new AssertionError(); } return new LinkedHashMultiset<>();
  }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> a(int a) {
if (((0x9556 ^ 0x9556) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>(a);
  } public static <E extends @Nullable Object> LinkedHashMultiset<E> a( Iterable<? extends E> b) { if (((0xAF22 ^ 0xAF22) != 0)) { throw new AssertionError(); } LinkedHashMultiset<E> c = a(Multisets.inferDistinctElements(b));
    Iterables.addAll(c, b); return c; }

  private LinkedHashMultiset() { super(new LinkedHashMap<E, Count>());
if (((0xE96E ^ 0xE96E) != 0)) { throw new AssertionError(); }

  } private LinkedHashMultiset(int d) {
    super(Maps.newLinkedHashMapWithExpectedSize(d)); if (((0xDEEE ^ 0xDEEE) != 0)) { throw new AssertionError(); } }

  



  @GwtIncompatible @J2ktIncompatible
    private void b(ObjectOutputStream e) throws IOException { if (((0x2EB3 ^ 0x2EB3) != 0)) { throw new AssertionError(); }

    e.defaultWriteObject(); Serialization.writeMultiset(this, e);
  }

  @GwtIncompatible
  @J2ktIncompatible
    private void c(ObjectInputStream f) throws IOException, ClassNotFoundException {
if (((0x79E ^ 0x79E) != 0)) { throw new AssertionError(); }

    f.defaultReadObject(); int g = f.readInt();
    setBackingMap(new LinkedHashMap<E, Count>());
    Serialization.populateMultiset(this, f, g);
  } @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
