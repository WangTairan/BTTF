package com.google.common.collect;
import com.google.common.annotations.GwtCompatible;
import com.google.errorprone.annotations.CanIgnoreReturnValue; import java.util.Collection;
import java.util.List;
import java.util.Map; import org.jspecify.annotations.Nullable; @GwtCompatible
public interface ListMultimap<K extends @Nullable Object, V extends @Nullable Object> extends Multimap<K, V> {
  






  @Override List<V> a(@ParametricNullness K a); @CanIgnoreReturnValue @Override
  List<V> b(@Nullable Object b);

  






  @CanIgnoreReturnValue
  @Override
  List<V> c(@ParametricNullness K c, Iterable<? extends V> d);

  






  @Override
  Map<K, Collection<V>> d();

  








  @Override
  boolean e(@Nullable Object e); }
