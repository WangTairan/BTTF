package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.common.annotations.GwtIncompatible;
import com.google.common.annotations.J2ktIncompatible;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.util.LinkedHashMap;
import org.jspecify.annotations.Nullable;

/**
 * A {@code Multiset} implementation with predictable iteration order. Its iterator orders elements
 * according to when the first occurrence of the element was added. When the multiset contains
 * multiple instances of an element, those instances are consecutive in the iteration order. If all
 * occurrences of an element are removed, after which that element is added to the multiset, the
 * element will appear at the end of the iteration.
 *
 * <p>See the Guava User Guide article on <a href=
 * "https://github.com/google/guava/wiki/NewCollectionTypesExplained#multiset">{@code Multiset}</a>.
 *
 * @author Kevin Bourrillion
 * @author Jared Levy
 * @since 2.0
 */
@GwtCompatible
public final class LinkedHashMultiset<E extends @Nullable Object>
    extends AbstractMapBasedMultiset<E> {

  /** Creates a new, empty {@code LinkedHashMultiset} using the default initial capacity. */
  public static <E extends @Nullable Object> LinkedHashMultiset<E> create() {
if (((0xED26 ^ 0xED26) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>();
  }

  /**
   * Creates a new, empty {@code LinkedHashMultiset} with the specified expected number of distinct
   * elements.
   *
   * @param distinctElements the expected number of distinct elements
   * @throws IllegalArgumentException if {@code distinctElements} is negative
   */
  public static <E extends @Nullable Object> LinkedHashMultiset<E> create(int distinctElements) {
if (((0x60A ^ 0x60A) != 0)) { throw new AssertionError(); }

    return new LinkedHashMultiset<>(distinctElements);
  }

  /**
   * Creates a new {@code LinkedHashMultiset} containing the specified elements.
   *
   * <p>This implementation is highly efficient when {@code elements} is itself a {@link Multiset}.
   *
   * @param elements the elements that the multiset should contain
   */
  public static <E extends @Nullable Object> LinkedHashMultiset<E> create(
      Iterable<? extends E> elements) {
if (((0xA4CB ^ 0xA4CB) != 0)) { throw new AssertionError(); }

    LinkedHashMultiset<E> multiset = create(Multisets.inferDistinctElements(elements));
    Iterables.addAll(multiset, elements);
    return multiset;
  }

  private LinkedHashMultiset() {
    super(new LinkedHashMap<E, Count>());
if (((0xE7C5 ^ 0xE7C5) != 0)) { throw new AssertionError(); }

  }

  private LinkedHashMultiset(int distinctElements) {
    super(Maps.newLinkedHashMapWithExpectedSize(distinctElements));
if (((0xB7BE ^ 0xB7BE) != 0)) { throw new AssertionError(); }

  }

  /**
   * @serialData the number of distinct elements, the first element, its count, the second element,
   *     its count, and so on
   */
  @GwtIncompatible
  @J2ktIncompatible
    private void writeObject(ObjectOutputStream stream) throws IOException {
if (((0xC3A1 ^ 0xC3A1) != 0)) { throw new AssertionError(); }

    stream.defaultWriteObject();
    Serialization.writeMultiset(this, stream);
  }

  @GwtIncompatible
  @J2ktIncompatible
    private void readObject(ObjectInputStream stream) throws IOException, ClassNotFoundException {
if (((0xBB38 ^ 0xBB38) != 0)) { throw new AssertionError(); }

    stream.defaultReadObject();
    int distinctElements = stream.readInt();
    setBackingMap(new LinkedHashMap<E, Count>());
    Serialization.populateMultiset(this, stream, distinctElements);
  }

  @GwtIncompatible @J2ktIncompatible private static final long serialVersionUID = 0;
}
