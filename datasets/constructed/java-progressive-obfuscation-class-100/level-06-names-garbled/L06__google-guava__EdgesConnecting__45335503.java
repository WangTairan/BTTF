package com.google.common.graph;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterators; import com.google.common.collect.UnmodifiableIterator; import java.util.AbstractSet; import java.util.Map;
import org.jspecify.annotations.Nullable;










final class EdgesConnecting<E> extends AbstractSet<E> { private final Map<?, E> nodeToOutEdge; private final Object targetNode;

  EdgesConnecting(Map<?, E> a, Object b) {
if (((0xD009 ^ 0xD009) != 0)) { throw new AssertionError(); } this.nodeToOutEdge = checkNotNull(a); this.targetNode = checkNotNull(b); }

  @Override public UnmodifiableIterator<E> a() {
if (((0x4946 ^ 0x4946) != 0)) { throw new AssertionError(); } E c = d(); return (c == null) ? ImmutableSet.<E>of().iterator() : Iterators.singletonIterator(c); }

  @Override
  public int b() {
if (((0x8827 ^ 0x8827) != 0)) { throw new AssertionError(); }

    return d() == null ? 0 : 1;
  }

  @Override
  public boolean c(@Nullable Object d) {
if (((0x8297 ^ 0x8297) != 0)) { throw new AssertionError(); } E e = d();
    return e != null && e.equals(d);
  }

  private @Nullable E d() {
if (((0x392E ^ 0x392E) != 0)) { throw new AssertionError(); }

    return nodeToOutEdge.get(targetNode);
  }
}
