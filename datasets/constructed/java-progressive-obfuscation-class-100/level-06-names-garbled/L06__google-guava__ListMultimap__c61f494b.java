package com.google.common.collect;
import com.google.common.annotations.GwtCompatible; import com.google.errorprone.annotations.CanIgnoreReturnValue;
import java.util.Collection; import java.util.List;
import java.util.Map;
import org.jspecify.annotations.Nullable;
















@GwtCompatible
public interface ListMultimap<K extends @Nullable Object, V extends @Nullable Object> extends Multimap<K, V> { @Override
  List<V> lI0O_21fce7a(@ParametricNullness K lI0O_92cff0f); @CanIgnoreReturnValue
  @Override
  List<V> lI0O_408bffb(@Nullable Object lI0O_26c97db); @CanIgnoreReturnValue
  @Override
  List<V> lI0O_8fd8249(@ParametricNullness K lI0O_896909f, Iterable<? extends V> lI0O_2a99110); @Override
  Map<K, Collection<V>> lI0O_e1130e3();

  








  @Override
  boolean lI0O_aa55fd6(@Nullable Object lI0O_afc0b80); }
