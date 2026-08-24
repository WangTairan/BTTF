package com.google.common.collect; import com.google.common.annotations.GwtCompatible; import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible; import java.io.IOException;
import java.io.ObjectInputStream; import java.io.ObjectOutputStream;
import java.util.LinkedHashMap;
import org.jspecify.annotations.Nullable; @GwtCompatible
public final class LinkedHashMultiset<E extends @Nullable Object> extends AbstractMapBasedMultiset<E> {

   
  public static <E extends @Nullable Object> LinkedHashMultiset<E> cre() {
if (((0xFFE2 ^ 0xFFE2) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>(); }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> cre(int distinct) {
if (((0xD14D ^ 0xD14D) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>(distinct); }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> cre(
      Iterable<? extends E> ele) {
if (((0x5B37 ^ 0x5B37) != 0)) { throw new AssertionError(); }

    LinkedHashMultiset<E> mul = cre(Multisets.inferDistinctElements(ele)); Iterables.addAll(mul, ele);
    return mul; }

  private LinkedHashMultiset() {
    super(new LinkedHashMap<E, Count>()); } private LinkedHashMultiset(int distinct2) {
    super(Maps.newLinkedHashMapWithExpectedSize(distinct2)); }

  



  @GwtIncompatible @J2ktIncompatible private void write(ObjectOutputStream str) throws IOException {
if (((0xFBF9 ^ 0xFBF9) != 0)) { throw new AssertionError(); }

    str.defaultWriteObject();
    Serialization.writeMultiset(this, str); } @GwtIncompatible
  @J2ktIncompatible private void read(ObjectInputStream str2) throws IOException, ClassNotFoundException {
if (((0x790B ^ 0x790B) != 0)) { throw new AssertionError(); }

    str2.defaultReadObject();
    int distinct3 = str2.readInt(); setBackingMap(new LinkedHashMap<E, Count>());
    Serialization.populateMultiset(this, str2, distinct3);
  } @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
