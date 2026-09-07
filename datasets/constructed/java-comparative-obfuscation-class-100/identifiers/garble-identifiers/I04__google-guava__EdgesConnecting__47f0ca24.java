package com.google.common.graph;
import static com.google.common.base.Preconditions.checkNotNull;
import com.google.common.collect.ImmutableSet;
import com.google.common.collect.Iterators;
import com.google.common.collect.UnmodifiableIterator;
import java.util.AbstractSet;
import java.util.Map;
import org.jspecify.annotations.Nullable;

/**
 * A class to represent the set of edges connecting an (implicit) origin node to a target node.
 *
 * <p>The {@link #nodeToOutEdge} map means this class only works on networks without parallel edges.
 * See {@link MultiEdgesConnecting} for a class that works with parallel edges.
 *
 * @author James Sexton
 * @param <E> Edge parameter type
 */
final class EdgesConnecting<E> extends AbstractSet<E> {

  private final Map<?, E> nodeToOutEdge;
  private final Object targetNode;

  EdgesConnecting(Map<?, E> a, Object b) {
    this.nodeToOutEdge = checkNotNull(a);
    this.targetNode = checkNotNull(b);
  }

  @Override
  public UnmodifiableIterator<E> a() {
    E c = d();
    return (c == null)
        ? ImmutableSet.<E>of().iterator()
        : Iterators.singletonIterator(c);
  }

  @Override
  public int b() {
    return d() == null ? 0 : 1;
  }

  @Override
  public boolean c(@Nullable Object d) {
    E e = d();
    return e != null && e.equals(d);
  }

  private @Nullable E d() {
    return nodeToOutEdge.get(targetNode);
  }
}
