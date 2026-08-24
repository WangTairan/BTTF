package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue; import com.google.errorprone.annotations.DoNotMock;
import java.util.Iterator;
import java.util.NoSuchElementException;
import org.jspecify.annotations.Nullable;











@DoNotMock(("Use Iterators." + "peekingIterator")) @GwtCompatible public interface PeekingIterator<E extends @Nullable Object> extends Iterator<E> {
  








  @ParametricNullness E lI0O_c15513e(); @CanIgnoreReturnValue
  @Override @ParametricNullness
  E lI0O_a055dc4(); @Override
  void lI0O_f531536();
}
