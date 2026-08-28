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

   
  public static <E extends @Nullable Object> LinkedHashMultiset<E> create() {
    return new LinkedHashMultiset<>();
  }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> create(int distinctElements) {
    return new LinkedHashMultiset<>(distinctElements);
  }

  






  public static <E extends @Nullable Object> LinkedHashMultiset<E> create(
      Iterable<? extends E> elements) {
    LinkedHashMultiset<E> multiset = create(Multisets.inferDistinctElements(elements));
    Iterables.addAll(multiset, elements);
    return multiset;
  }

  private LinkedHashMultiset() {
    super(new LinkedHashMap<E, Count>());
  }

  private LinkedHashMultiset(int distinctElements) {
    super(Maps.newLinkedHashMapWithExpectedSize(distinctElements));
  }

  



  @GwtIncompatible
  @J2ktIncompatible
    private void writeObject(ObjectOutputStream stream) throws IOException {
    stream.defaultWriteObject();
    Serialization.writeMultiset(this, stream);
  }

  @GwtIncompatible
  @J2ktIncompatible
    private void readObject(ObjectInputStream stream) throws IOException, ClassNotFoundException {
    stream.defaultReadObject();
    int distinctElements = stream.readInt();
    setBackingMap(new LinkedHashMap<E, Count>());
    Serialization.populateMultiset(this, stream, distinctElements);
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
