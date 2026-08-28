package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue; import java.util.Collection;
import java.util.List;
import java.util.Map; import org.jspecify.annotations.Nullable; @GwtCompatible
public interface ListMultimap<K extends @Nullable Object, V extends @Nullable Object> extends Multimap<K, V> {
  






  @Override List<V> get(@ParametricNullness K key); @CanIgnoreReturnValue @Override
  List<V> remove(@Nullable Object key);

  






  @CanIgnoreReturnValue
  @Override
  List<V> replace(@ParametricNullness K key, Iterable<? extends V> val);

  






  @Override
  Map<K, Collection<V>> as();

  








  @Override
  boolean equ(@Nullable Object obj); }
