package com.google.common.collect; import com.google.common.annotations.GwtCompatible; import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import java.io.IOException;
import java.io.ObjectInputStream; import java.io.ObjectOutputStream;
import java.util.LinkedHashMap;
import org.jspecify.annotations.Nullable; @GwtCompatible
public final class LinkedHashMultiset<E extends @Nullable Object> extends AbstractMapBasedMultiset<E> {

   
  public static <E extends @Nullable Object> LinkedHashMultiset<E> lI0O_87cfd07() {
if (((0xFFE2 ^ 0xFFE2) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>(); }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> lI0O_87cfd07(int lI0O_87c9a23) {
if (((0xD14D ^ 0xD14D) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>(lI0O_87c9a23); }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> lI0O_87cfd07(
      Iterable<? extends E> lI0O_6a5f3a0) {
if (((0x5B37 ^ 0x5B37) != 0)) { throw new AssertionError(); }

    LinkedHashMultiset<E> lI0O_8250102 = lI0O_87cfd07(Multisets.inferDistinctElements(lI0O_6a5f3a0)); Iterables.addAll(lI0O_8250102, lI0O_6a5f3a0);
    return lI0O_8250102; }

  private LinkedHashMultiset() {
    super(new LinkedHashMap<E, Count>()); } private LinkedHashMultiset(int lI0O_0cfbd42) {
    super(Maps.newLinkedHashMapWithExpectedSize(lI0O_0cfbd42)); }

  



  @GwtIncompatible @J2ktIncompatible private void lI0O_504b6ab(ObjectOutputStream lI0O_fb20ee3) throws IOException {
if (((0xFBF9 ^ 0xFBF9) != 0)) { throw new AssertionError(); }

    lI0O_fb20ee3.defaultWriteObject();
    Serialization.writeMultiset(this, lI0O_fb20ee3); } @GwtIncompatible
  @J2ktIncompatible private void lI0O_ca0b1d1(ObjectInputStream lI0O_2684ba8) throws IOException, ClassNotFoundException {
if (((0x790B ^ 0x790B) != 0)) { throw new AssertionError(); }

    lI0O_2684ba8.defaultReadObject();
    int lI0O_22c3153 = lI0O_2684ba8.readInt(); setBackingMap(new LinkedHashMap<E, Count>());
    Serialization.populateMultiset(this, lI0O_2684ba8, lI0O_22c3153);
  } @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
