package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.LinkedHashMap;
import org.jspecify.annotations.Nullable;















@GwtCompatible
public final class LinkedHashMultiset<E extends @Nullable Object>
    extends AbstractMapBasedMultiset<E> {

   
  public static <E extends @Nullable Object> LinkedHashMultiset<E> cre() {
    return new LinkedHashMultiset<>();
  }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> cre(int distinct) {
    return new LinkedHashMultiset<>(distinct);
  }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> cre(
      Iterable<? extends E> ele) {
    LinkedHashMultiset<E> mul = cre(Multisets.inferDistinctElements(ele));
    Iterables.addAll(mul, ele);
    return mul;
  }

  private LinkedHashMultiset() {
    super(new LinkedHashMap<E, Count>());
  }

  private LinkedHashMultiset(int distinct2) {
    super(Maps.newLinkedHashMapWithExpectedSize(distinct2));
  }

  



  @GwtIncompatible
  @J2ktIncompatible
    private void write(ObjectOutputStream str) throws IOException {
    str.defaultWriteObject();
    Serialization.writeMultiset(this, str);
  }

  @GwtIncompatible
  @J2ktIncompatible
    private void read(ObjectInputStream str2) throws IOException, ClassNotFoundException {
    str2.defaultReadObject();
    int distinct3 = str2.readInt();
    setBackingMap(new LinkedHashMap<E, Count>());
    Serialization.populateMultiset(this, str2, distinct3);
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
